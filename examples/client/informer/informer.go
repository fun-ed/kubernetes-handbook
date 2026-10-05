package main

import (
	"context"
	"errors"
	"flag"
	"fmt"
	"os"
	"os/signal"
	"path/filepath"
	"syscall"
	"time"

	"k8s.io/api/core/v1"
	"k8s.io/client-go/informers"
	coreinformers "k8s.io/client-go/informers/core/v1"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/tools/cache"
	"k8s.io/client-go/tools/clientcmd"
	"k8s.io/component-base/logs"
	klog "k8s.io/klog/v2"
)

// PodLoggingController logs the name and namespace of pods that are added,
// deleted, or updated
type PodLoggingController struct {
	informerFactory informers.SharedInformerFactory
	podInformer     coreinformers.PodInformer
	handler         cache.ResourceEventHandlerRegistration
}

// Run starts shared informers, waits for their caches and event handler to
// synchronize, then runs until ctx is cancelled.
func (c *PodLoggingController) Run(ctx context.Context) error {
	c.informerFactory.StartWithContext(ctx)

	synced := c.informerFactory.WaitForCacheSyncWithContext(ctx)
	if synced.Err != nil {
		return fmt.Errorf("wait for informer caches to sync: %w", synced.Err)
	}
	if !cache.WaitFor(ctx, "pod event handler sync", c.handler.HasSyncedChecker()) {
		return fmt.Errorf("wait for pod event handler to sync: %w", context.Cause(ctx))
	}

	<-ctx.Done()
	return nil
}

func (c *PodLoggingController) podAdd(obj interface{}) {
	pod := obj.(*v1.Pod)
	klog.Infof("POD CREATED: %s/%s", pod.Namespace, pod.Name)
}

func (c *PodLoggingController) podUpdate(old, new interface{}) {
	oldPod := old.(*v1.Pod)
	newPod := new.(*v1.Pod)
	klog.Infof(
		"POD UPDATED. %s/%s %s",
		oldPod.Namespace, oldPod.Name, newPod.Status.Phase,
	)
}

func (c *PodLoggingController) podDelete(obj interface{}) {
	key, err := cache.DeletionHandlingMetaNamespaceKeyFunc(obj)
	if err != nil {
		klog.ErrorS(err, "Ignoring invalid pod delete notification")
		return
	}
	klog.Infof("POD DELETED: %s", key)
}

// NewPodLoggingController creates a PodLoggingController
func NewPodLoggingController(informerFactory informers.SharedInformerFactory) (*PodLoggingController, error) {
	podInformer := informerFactory.Core().V1().Pods()

	c := &PodLoggingController{
		informerFactory: informerFactory,
		podInformer:     podInformer,
	}
	registration, err := podInformer.Informer().AddEventHandler(
		// Your custom resource event handlers.
		cache.ResourceEventHandlerFuncs{
			// Called on creation
			AddFunc: c.podAdd,
			// Called on resource update and every resyncPeriod on existing resources.
			UpdateFunc: c.podUpdate,
			// Called on resource deletion.
			DeleteFunc: c.podDelete,
		},
	)
	if err != nil {
		return nil, err
	}

	c.handler = registration
	return c, nil
}

var kubeconfig string

func init() {
	flag.StringVar(&kubeconfig, "kubeconfig", filepath.Join(os.Getenv("HOME"), ".kube", "config"), "absolute path to the kubeconfig file")
}

func main() {
	if err := run(); err != nil {
		fmt.Fprintf(os.Stderr, "informer: %v\n", err)
		os.Exit(1)
	}
}

func run() error {
	flag.Parse()
	logs.InitLogs()
	defer logs.FlushLogs()

	ctx, cancel := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer cancel()

	config, err := clientcmd.BuildConfigFromFlags("", kubeconfig)
	if err != nil {
		return fmt.Errorf("build Kubernetes config: %w", err)
	}

	clientset, err := kubernetes.NewForConfig(config)
	if err != nil {
		return fmt.Errorf("create Kubernetes client: %w", err)
	}

	factory := informers.NewSharedInformerFactory(clientset, 24*time.Hour)
	defer factory.Shutdown()

	controller, err := NewPodLoggingController(factory)
	if err != nil {
		return fmt.Errorf("create Pod logging controller: %w", err)
	}

	if err := controller.Run(ctx); err != nil && !errors.Is(err, context.Canceled) {
		return err
	}
	return nil
}
