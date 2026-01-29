# ADR-001: Parser Architecture & Domain Models

## Status
Decided

## Context
The project requires a reliable way to extract structured data from PDF credit card statements. Early implementations proved that coordinate-aware line normalization is necessary. As we move towards full parsing, we need a flexible architecture that can handle multi-page statements, interleaved sections (transactions vs rewards), and multiple bank providers.

## Decision
1.  **State Machine Parser**: Implement a state machine (`HEADER`, `TRANSACTIONS`, `REWARDS`, `FOOTER`) to drive the parsing logic. This allows the parser to maintain context (e.g., current transaction being built) across multiple lines.
2.  **Pydantic Domain Models**: Define the target schema using Pydantic classes. This provides automatic validation, IDE support, and standard JSON serialization.
3.  **Separation of Concerns**:
    *   **Normalizer**: Responsible for geometry-to-text conversion (coordinate-based grouping).
    *   **Parser**: Responsible for semantics-to-data conversion (state-based transitions).
    *   **Models**: Pure data definitions.

## Consequences
*   **Pros**:
    *   Easier to add new providers by defining new state transition rules.
    *   Strict validation of the final JSON output.
    *   Robust handling of multi-line transaction descriptions (e.g., FX details).
*   **Cons**:
    *   Slightly more complex than simple regex-based linear parsing.
    *   Requires detailed upfront model definition.
