// Command validate-crds validates CRD definitions using Kubernetes' pinned API library.
package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"runtime/debug"

	apiextensions "k8s.io/apiextensions-apiserver/pkg/apis/apiextensions"
	apiextensionsinstall "k8s.io/apiextensions-apiserver/pkg/apis/apiextensions/install"
	apiextensionsv1 "k8s.io/apiextensions-apiserver/pkg/apis/apiextensions/v1"
	apiextensionsvalidation "k8s.io/apiextensions-apiserver/pkg/apis/apiextensions/validation"
	"k8s.io/apimachinery/pkg/runtime"
)

const moduleVersion = "v0.37.1"

type request struct {
	ID       string          `json:"id"`
	Source   string          `json:"source"`
	Document string          `json:"document"`
	Body     json.RawMessage `json:"body"`
}

type issue struct {
	Field  string `json:"field"`
	Type   string `json:"type"`
	Detail string `json:"detail"`
}

type result struct {
	ID     string  `json:"id"`
	Errors []issue `json:"errors"`
}

type response struct {
	ModuleVersion string   `json:"module_version"`
	Results       []result `json:"results"`
}

func decodeStrict(data []byte, target any) error {
	decoder := json.NewDecoder(bytes.NewReader(data))
	decoder.DisallowUnknownFields()
	if err := decoder.Decode(target); err != nil {
		return err
	}
	var extra any
	if err := decoder.Decode(&extra); err != io.EOF {
		if err == nil {
			return fmt.Errorf("multiple JSON values")
		}
		return err
	}
	return nil
}

func validate(input request, scheme *runtime.Scheme) result {
	out := result{ID: input.ID, Errors: []issue{}}
	var obj apiextensionsv1.CustomResourceDefinition
	if err := decodeStrict(input.Body, &obj); err != nil {
		out.Errors = append(out.Errors, issue{Field: "", Type: "DecodeError", Detail: "CRD JSON has unknown fields or invalid encoding"})
		return out
	}
	if obj.APIVersion != "apiextensions.k8s.io/v1" {
		out.Errors = append(out.Errors, issue{Field: "apiVersion", Type: "Invalid", Detail: "must be apiextensions.k8s.io/v1"})
	}
	if obj.Kind != "CustomResourceDefinition" {
		out.Errors = append(out.Errors, issue{Field: "kind", Type: "Invalid", Detail: "must be CustomResourceDefinition"})
	}
	if obj.Name == "" {
		out.Errors = append(out.Errors, issue{Field: "metadata.name", Type: "Required", Detail: "must be specified"})
	}
	if len(out.Errors) > 0 {
		return out
	}

	// Scheme defaults mirror Kubernetes' create-time CRD defaults, including listKind,
	// conversion strategy, and status.storedVersions, before internal conversion.
	scheme.Default(&obj)
	internal := &apiextensions.CustomResourceDefinition{}
	if err := scheme.Convert(&obj, internal, nil); err != nil {
		out.Errors = append(out.Errors, issue{Field: "", Type: "ConversionError", Detail: "official CRD conversion failed"})
		return out
	}
	for _, validationError := range apiextensionsvalidation.ValidateCustomResourceDefinition(context.Background(), internal) {
		out.Errors = append(out.Errors, issue{
			Field:  validationError.Field,
			Type:   string(validationError.Type),
			Detail: validationError.Detail,
		})
	}
	return out
}

func requirePinnedModuleVersion() error {
	info, ok := debug.ReadBuildInfo()
	if !ok {
		return fmt.Errorf("cannot inspect Go module build information")
	}
	for _, dependency := range info.Deps {
		if dependency.Path == "k8s.io/apiextensions-apiserver" {
			if dependency.Version != moduleVersion || dependency.Replace != nil {
				return fmt.Errorf("expected k8s.io/apiextensions-apiserver %s, found %s", moduleVersion, dependency.Version)
			}
			return nil
		}
	}
	return fmt.Errorf("k8s.io/apiextensions-apiserver is absent from Go module build information")
}

func run() error {
	decoder := json.NewDecoder(os.Stdin)
	decoder.DisallowUnknownFields()
	var requests []request
	if err := decoder.Decode(&requests); err != nil {
		return fmt.Errorf("decode request array: %w", err)
	}
	var extra any
	if err := decoder.Decode(&extra); err != io.EOF {
		if err == nil {
			return fmt.Errorf("multiple request JSON values")
		}
		return fmt.Errorf("trailing request data: %w", err)
	}
	if err := requirePinnedModuleVersion(); err != nil {
		return err
	}
	scheme := runtime.NewScheme()
	apiextensionsinstall.Install(scheme)
	response := response{ModuleVersion: moduleVersion, Results: make([]result, 0, len(requests))}
	for _, item := range requests {
		response.Results = append(response.Results, validate(item, scheme))
	}
	encoder := json.NewEncoder(os.Stdout)
	encoder.SetEscapeHTML(false)
	return encoder.Encode(response)
}

func main() {
	if err := run(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
