---
name: google-rust-style
description: "Enforce Google's official production Rust Style Guide and API design rules for large-scale codebases. Covers flexible references, newtypes over type aliases, non-exhaustive enums, ownership/borrowing (minimizing Rc/Arc), error handling (Option vs Result vs panic), crate modularity, and compiler scalability."
version: 1.0.0
author: Krishna Kanth
license: MIT
metadata:
  icon: "🦀"
hermes:
  tags: [rust, google-style, api-design, safety, architecture, systems-programming, code-quality]
---

# 🦀 Google Rust Style Guide & API Design Rules

Guidelines codified from Google's internal production Rust style guide, engineered for massive distributed codebases (Android, Chromium) prioritizing long-term maintainability, compiler scalability, and cross-team interface stability over write-time convenience.

Official Reference: [Google Rust Style Guide](https://google.github.io/styleguide/rustguide.html)

---

## 🎯 Core Engineering Principles

1. **Readability and Maintainability over Writability**: Code is read and maintained far more often than written. Prefer clarity and compiler-verified correctness over clever shortcuts.
2. **Ecosystem Alignment**: Follow standard Rust conventions ([Rust API Guidelines](https://rust-lang.github.io/api-guidelines/) & `rustfmt`) unless explicitly adjusted for large-scale enterprise constraints.
3. **Justifiable Rules**: Every guideline exists to prevent verified production incidents, avoid pointless review debates, or speed up distributed builds.

---

## 📐 1. API Design & Function Signatures

### Accept Flexible References for Immutable Data
Never accept references to smart pointers, containers, or owned wrappers when the underlying slice or reference suffices.

* ❌ **Anti-pattern**:
  ```rust
  fn process_text(s: &String) { ... }
  fn parse_items(items: &Vec<Item>) { ... }
  fn read_data(boxed: &Box<Config>) { ... }
  fn check_value(opt: &Option<Value>) { ... }
  ```
* ✅ **Idiomatic Google Style**:
  ```rust
  fn process_text(s: &str) { ... }
  fn parse_items(items: &[Item]) { ... }
  fn read_data(config: &Config) { ... }
  fn check_value(opt: Option<&Value>) { ... } // or accept &Value directly
  ```
* **Rationale**: Callers should not be forced into allocations, conversions, or specific wrapper layouts to invoke a read-only function.

### Prefer Enums over Booleans in Public APIs
Boolean flags obscure intent at call sites (`connect(true, false)`).
* ❌ **Anti-pattern**: `fn set_visibility(visible: bool)`
* ✅ **Idiomatic Google Style**:
  ```rust
  pub enum Visibility {
      Visible,
      Hidden,
  }
  fn set_visibility(visibility: Visibility) { ... }
  ```

### Accept `Into<T>` Responsibly
Accept generic `impl Into<T>` parameters only when the conversion is cheap, unambiguous, and significantly improves ergonomics for common caller types (e.g., `impl Into<PathBuf>` or `impl Into<String>`).

---

## 🧱 2. Types & Data Modeling

### Newtypes over Type Aliases
Use tuple structs (the newtype pattern) instead of `type Alias = Target;` whenever:
1. The types carry distinct semantic domain meaning.
2. The type warrants domain-specific methods or invariant validation.
3. Callers could accidentally swap arguments of identical primitive types.

* ❌ **Anti-pattern**:
  ```rust
  type Days = u32;
  type Months = u32;
  fn schedule(days: Days, months: Months) { ... } // Easy to swap accidentally
  ```
* ✅ **Idiomatic Google Style**:
  ```rust
  #[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
  pub struct Days(pub u32);

  #[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
  pub struct Months(pub u32);

  fn schedule(days: Days, months: Months) { ... }
  ```

### Struct Layouts
* Prefer **named fields** over tuples and multi-field tuple structs. Tuple structs should be reserved for single-field newtypes.
* Configuration and options structs must always implement `Default`.

---

## 🚦 3. Error Reporting Conventions

| Category | Recommended Pattern | Example |
| :--- | :--- | :--- |
| **Simple / Anticipated Failure** | `Option<T>` | `checked_add` returning `None` on overflow; missing key in a map. Extra error details provide zero diagnostic value. |
| **Recoverable Failure** | `Result<T, E>` | I/O errors, network timeouts, invalid syntax. Returns actionable context to caller. |
| **Contract / Invariant Violation** | `panic!` | Reaching logically unreachable code, corrupted internal state, or programmer API contract breach. |

### Pattern Matching over Check-Then-Unwrap
Never inspect a state with an `if` check only to call `.unwrap()` inside.
* ❌ **Anti-pattern**:
  ```rust
  if value.is_some() {
      let inner = value.unwrap();
      process(inner);
  }
  ```
* ✅ **Idiomatic Google Style**:
  ```rust
  if let Some(inner) = value {
      process(inner);
  }
  ```
* **Rationale**: Eliminates potential panics if subsequent refactorings detach the check from the unwrap.

### Prefer `expect` with Descriptive Context over `unwrap`
When a value is guaranteed to exist by design but cannot be proven to the compiler, use `.expect("invariant description")` explaining *why* it is guaranteed, rather than an unadorned `.unwrap()`.

---

## 🧠 4. Ownership, Memory & Concurrency

### Avoid `Rc` and `Arc` by Default
* Default to **unique ownership** or **borrowing**.
* Do not introduce reference-counted pointers as a crutch to bypass borrow checker learning curves.
* **Exception**: Introduce `Rc`/`Arc` only when strict borrowing creates unreasonable structural lifetime complexity across asynchronous boundaries or multi-owner acyclic graph topologies.

### Prefer Borrows over Deep Clones
* Avoid `.clone()` in hot paths unless ownership transfer is fundamentally required.
* Pass data by reference when the callee only needs to inspect or project data.

---

## 🌐 5. Public API Stability & Compiler Scalability

### Apply `#[non_exhaustive]` on Public Enums & Structs
Public enums exposed across crate/team boundaries must be marked with `#[non_exhaustive]`.
```rust
#[non_exhaustive]
pub enum ErrorKind {
    NotFound,
    PermissionDenied,
    Timeout,
}
```
* **Rationale**: Prevents breaking downstream consumers when new variants are introduced in future releases, forcing callers to implement a wildcard fallback arm (`_ => ...`).
* **Exceptions**: Closed domains that are mathematically complete (e.g., RGB colors, boolean-equivalent two-state enums).

### Prefer Small Crates (Chromium / Monorepo Scalability)
* In large monorepos, crates serve as the atomic unit of compilation.
* Large monolithic crates bottleneck parallel build queues and invalidate coarse build caches.
* Decompose crates into fine-grained units (in extreme monorepo environments like Chromium, single-purpose or single-file crates) to maximize distributed compilation parallelism.

### Import Hygiene
* **Qualify top-level function calls**: Call free functions with their module name (`fs::read(...)`, not `read(...)`).
* **Import type names unqualified**: Import struct, enum, and trait names directly (`use std::path::PathBuf;` -> `PathBuf`).
* **No glob imports**: Avoid `use module::*`. Explicitly name imported symbols to prevent namespace pollution and silent name-shadowing breakages during dependency upgrades.
