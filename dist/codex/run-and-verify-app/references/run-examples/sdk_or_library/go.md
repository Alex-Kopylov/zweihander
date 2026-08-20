# Example: Go SDK / Library

Go libraries do not usually have a long-running "run" surface. For Go SDKs and
libraries, the run skill is about:

1. **Building** the package from source
2. **Running the test suite**
3. **A minimal consumer program** that imports the module and exercises one
   public API

Keep it brief. The template's Build and Test sections do most of the work.

## The smoke-test example

The Go-specific addition is a tiny consumer module. It proves that the package
works from the outside, not just from its internal tests:

> ## Verify
>
> ```bash
> tmp=$(mktemp -d)
> cat > "$tmp/go.mod" <<'GO'
> module smoke
>
> require example.com/mylib v0.0.0
> replace example.com/mylib => /absolute/path/to/mylib
> GO
> cat > "$tmp/main.go" <<'GO'
> package main
>
> import "example.com/mylib"
>
> func main() {
> 	println(mylib.Version())
> }
> GO
> (cd "$tmp" && go mod tidy && go run .)
> # -> v1.2.3
> ```

## Example snippet

> ---
> name: run-mylib
> description: Build and test the mylib Go module from source. Use when asked to verify mylib works, run its tests, or build its packages.
> ---
>
> `mylib` is a Go library. "Running" it means building the packages,
> executing tests, and importing it from a minimal consumer module.
>
> ## Verify
>
> ```bash
> tmp=$(mktemp -d)
> cat > "$tmp/go.mod" <<'GO'
> module smoke
>
> require example.com/mylib v0.0.0
> replace example.com/mylib => /absolute/path/to/mylib
> GO
> cat > "$tmp/main.go" <<'GO'
> package main
>
> import "example.com/mylib"
>
> func main() {
> 	println(mylib.Version())
> }
> GO
> (cd "$tmp" && go mod tidy && go run .)
> ```
>
> ## Test
>
> ```bash
> go test ./...
> ```
>
> ## Build
>
> ```bash
> go build ./...
> ```

## Things to consider documenting

- **Module path.** Use the real module path from `go.mod`, and use `replace`
  only when the smoke module lives outside the checked-out repository.
- **Generated code.** If `go generate ./...`, protobuf, OpenAPI generation, or
  mock generation is required before build/test, document the exact command.
- **Build tags.** If tests or builds need tags such as `integration` or
  `sqlite`, include the exact `-tags` flag.
