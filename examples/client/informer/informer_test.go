package main

import (
	"testing"

	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/tools/cache"
)

func TestPodFromEvent(t *testing.T) {
	pod := &corev1.Pod{}
	var typedNil *corev1.Pod
	tests := []struct {
		name string
		obj  interface{}
		want *corev1.Pod
	}{
		{name: "valid pod", obj: pod, want: pod},
		{name: "nil interface", obj: nil},
		{name: "typed nil pod", obj: typedNil},
		{name: "wrong type", obj: "not a pod"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := podFromEvent(tt.obj, "test"); got != tt.want {
				t.Fatalf("podFromEvent(%T) = %p, want %p", tt.obj, got, tt.want)
			}
		})
	}
}

func TestInvalidPodNotificationsDoNotPanic(t *testing.T) {
	var typedNil *corev1.Pod
	validPod := &corev1.Pod{}
	tests := []struct {
		name string
		run  func()
	}{
		{name: "add valid pod", run: func() { (&PodLoggingController{}).podAdd(validPod) }},
		{name: "add nil interface", run: func() { (&PodLoggingController{}).podAdd(nil) }},
		{name: "add typed nil pod", run: func() { (&PodLoggingController{}).podAdd(typedNil) }},
		{name: "add wrong type", run: func() { (&PodLoggingController{}).podAdd("not a pod") }},
		{name: "update valid pods", run: func() { (&PodLoggingController{}).podUpdate(validPod, validPod) }},
		{name: "update invalid old object", run: func() { (&PodLoggingController{}).podUpdate("not a pod", validPod) }},
		{name: "update invalid new object", run: func() { (&PodLoggingController{}).podUpdate(validPod, nil) }},
		{name: "update both invalid", run: func() { (&PodLoggingController{}).podUpdate(typedNil, "not a pod") }},
		{name: "delete wrong type", run: func() { (&PodLoggingController{}).podDelete("not a pod") }},
		{name: "delete typed nil pod", run: func() { (&PodLoggingController{}).podDelete(typedNil) }},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			defer func() {
				if recovered := recover(); recovered != nil {
					t.Fatalf("notification panicked: %v", recovered)
				}
			}()
			tt.run()
		})
	}
}

func TestPodDeleteAcceptsPodAndDeletionTombstone(t *testing.T) {
	controller := &PodLoggingController{}
	controller.podDelete(&corev1.Pod{ObjectMeta: metav1.ObjectMeta{Namespace: "ns", Name: "pod"}})
	controller.podDelete(cache.DeletedFinalStateUnknown{Key: "ns/pod", Obj: nil})
}
