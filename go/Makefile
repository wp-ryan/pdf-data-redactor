# Makefile for PDF Redactor (Go version)

BINARY_NAME=pdf-redactor
PACKAGE=github.com/wp-ryan/pdf-data-redactor

.PHONY: all build clean test install

all: build

build:
	go build -o $(BINARY_NAME) .

install:
	go install

test:
	go test -v ./...

clean:
	go clean
	rm -f $(BINARY_NAME)

deps:
	go mod download

run: build
	./$(BINARY_NAME) --help

# Cross compilation
build-all:
	GOOS=linux GOARCH=amd64 go build -o $(BINARY_NAME)-linux-amd64 .
	GOOS=darwin GOARCH=amd64 go build -o $(BINARY_NAME)-darwin-amd64 .
	GOOS=windows GOARCH=amd64 go build -o $(BINARY_NAME)-windows-amd64.exe .
