# Orders Module

The `orders` module handles the domain logic and business processes related to customer orders. It demonstrates a complete implementation of CQRS, the Repository pattern, and Event-Driven Architecture within the BCor framework.

## Domain Model
- **`Order`**: The aggregate root managing order state (PENDING, SHIPPED).
- **`OrderState`**: Enum for tracking the order lifecycle.

## Communication
### Commands
- `CreateOrderCommand`: Triggers the creation of a new order aggregate.
- `ShipOrderCommand`: Transitions an existing order to the shipped state.

### Integration Events
- `OrderCreated`: Broadcasted when a new order is added to the system.
- `OrderShipped`: Broadcasted when an order's status changes to SHIPPED.

## Handlers
- `handle_create_order`: Validates order details and persists them using the Unit of Work.
- `handle_ship_order`: Implements state transition logic and error handling.

## Configuration
- `OrdersSettings`: Pydantic settings class for module-specific environment variables.
