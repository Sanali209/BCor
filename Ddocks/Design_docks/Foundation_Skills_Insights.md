# Foundation Template: Skills & Intelligence Insights

This document summarizes the high-level knowledge and architectural patterns encoded in the `foundation_template` skills. These represent "executable wisdom" that can be leveraged for high-quality development.

## 1. Executable Intelligence (The Script Pattern)
Most skills in `foundation_template` are not just static documentation; they include **automation scripts** that act as agent force-multipliers:
- **`senior-architect`**: Includes `architecture_diagram_generator.py` and `dependency_analyzer.py`.
- **`ui-ux-pro-max`**: Features a `search.py` script that generates a complete design system (palette, typography, landing structure) based on a simple query like "healthcare SaaS dashboard".
- **`project_architect.py`**: A general-purpose analysis tool mentioned across multiple skills for deep codebase optimization.

> [!TIP]
> **Takeaway**: Shift from "Read this doc" to "Run this script to analyze/generate X". This ensures best practices are applied consistently.

---

## 2. The 42 Rules of Clean Architecture
The `clean-architecture` skill contains 42 granular rule files, categorized by architectural impact.

### Core Priorities:
1. **Dependency Direction (Critical)**:
   - Source dependencies point **inward** only.
   - Interfaces belong to **clients**, not implementers (ISP).
   - Domain layer has **zero framework imports**.
2. **Entity Design (Critical)**:
   - Entities encapsulate **business invariants**, not just data.
   - **Rich Domain Models**: Avoid anemic data structures. Use "Value Objects" for domain concepts.
3. **Use Case Isolation (High)**:
   - Use cases **orchestrate entities** but do not implement core business logic themselves.
   - **Input/Output Ports**: Explicitly define what crosses the boundary.
4. **Component Cohesion**:
   - **Screaming Architecture**: The folder structure should reveal the domain (e.g., `orders/`, `billing/`), not the framework (e.g., `controllers/`, `models/`).

---

## 3. UI/UX "Pro Max" Intelligence
The UI skill is a comprehensive database of 50+ styles and 99 UX guidelines.

- **Systematic Selection**: Reasoning rules select styles (e.g., Glassmorphism vs. Minimalism) based on the industry and product type.
- **Master + Overrides Pattern**: Design decisions are persisted in a `MASTER.md` file, with page-specific deviations in a `pages/` directory. This ensures consistency while allowing necessary local flexibility.
- **Accessibility as Priority 1**: Contrast ratios, focus states, and keyboard navigation are treated as "Critical" (Priority 1) gates.

---

## 4. Architecture Patterns (Proven Blueprints)
The `architecture-patterns` skill codifies how to structure complex Python backends:
- **Clean Architecture Layers**:
    - `domain/`: Pure business logic, no framework imports. Use `abc.ABC` for interfaces (Ports).
    - `use_cases/`: Orchestrators (e.g., `CreateUserUseCase`).
    - `adapters/`: Implementation of ports (e.g., `PostgresUserRepository`).
- **DDD Tactical Patterns**:
    - **Value Objects**: Use `@dataclass(frozen=True)` with `__post_init__` for validation (e.g., `Email`, `Money`).
    - **Entities**: Objects with identity (e.g., `User(id=...)`).
    - **Aggregates**: Consistency boundaries (e.g., `Order` aggregate root).

## 5. Async Python Mastery
Extracted from `async-python-patterns` and its implementation playbook:
- **Robust Concurrency**: Use `asyncio.gather(*tasks, return_exceptions=True)` to prevent one failure from crashing the entire batch.
- **Rate Limiting**: Implement `asyncio.Semaphore(max_concurrent)` for API or DB operations.
- **Bridging Sync/Async**: Use `loop.run_in_executor` with a `ThreadPoolExecutor` for blocking I/O or CPU-heavy tasks within an async loop.
- **Mandatory Timeouts**: Wrap all external I/O in `asyncio.wait_for(..., timeout=N)`.

## 6. Type-First Development (Best Practices)
- **Make Illegal States Unrepresentable**: Use Discriminated Unions (`Idle | Loading | Success | Failure`) and `match` statements for exhaustive state handling.
- **Domain Primitives**: Use `NewType` for IDs (e.g., `UserId = NewType("UserId", str)`) to prevent logic errors like passing a `ProductId` to a `User` function.
- **Protocol**: Use `typing.Protocol` for structural typing (Go-style interfaces), allowing decoupling without explicit inheritance.
- **`ty` Runner**: Use `uvx ty check` for lightning-fast type checking compared to `mypy`.

## 7. Senior Architect "Executable Wisdom"
The `senior-architect` skill contains powerful Python-based automation scripts:
- **`architecture_diagram_generator.py`**: Scaffolds system diagrams.
- **`project_architect.py`**: Performs deep codebase analysis and optimization recommendations.
- **`dependency_analyzer.py`**: Maps out complex internal and external dependencies.

---

## 9. Game Design & UX Philosophy
Insights from `game-ui-design` and `level-design`:
- **Clarity in Chaos**: UI must be readable at peak intensity. If the player notices the UI, it's failing.
- **The "Build -> Peak -> Rest" Loop**: Level pacing should alternate between building tension, peak challenge (Boss/Combat), and rest (resource replenishment/story).
- **Diegetic Immersion**: Explore "in-world" UI (e.g., ammo counters on weapon models) to preserve immersion.
- **Teaching without Tutorials**: Introduce mechanics in "safe" zones (no risk of death) before combining them with lethal threats.
- **Visual Pathfinding**: Use high-contrast lighting and unique "landmarks" to guide players without explicit markers.

## 10. Native Mobile UX (Expo/React Native)
- **Apple "Zoom" Transitions**: Use standard iOS 18+ fluidity for a premium feel.
- **Contextual Navigation**: Frequent use of long-press context menus (`Link.Menu`) and link previews (`Link.Preview`) to follow platform conventions.
- **SF Symbols Integration**: Use native SF Symbols with weight and animation support for a truly "Apple-native" aesthetic.
- **Safe Area Mastery**: Use `contentInsetAdjustmentBehavior="automatic"` on scrollable elements instead of blunt `SafeAreaView` wrappers.

---

## 11. Final Integration Road Map
1. **Apply Architecture Rules**: Use the 42 Clean Architecture rules during the next refactor of BCor's core modules.
2. **Execute Analysis Scripts**: Run `project_architect.py` and `dependency_analyzer.py` on BCor to establish a technical debt baseline.
3. **Type-First Pivot**: Mandate `NewType` for domain IDs and `Protocol` for system-wide interfaces.
4. **Game Pacing Review**: Audit existing game mechanics against the "Intensity Graph" pattern for better engagement.
