from dataclasses import dataclass


@dataclass(frozen=True)
class RouteTarget:
    route: str
    screen: str
    ranking_id: int | None = None


def route_stack(route: str | None) -> list[RouteTarget]:
    normalized = (route or "/").split("?", 1)[0].rstrip("/") or "/"
    stack = [RouteTarget("/", "home")]

    if normalized == "/settings":
        return [*stack, RouteTarget("/settings", "settings")]
    if normalized == "/rankings/new":
        return [*stack, RouteTarget("/rankings/new", "create_ranking")]

    parts = normalized.strip("/").split("/")
    if len(parts) < 2 or parts[0] != "rankings":
        return stack

    try:
        ranking_id = int(parts[1])
    except ValueError:
        return stack
    if ranking_id <= 0:
        return stack

    ranking_route = f"/rankings/{ranking_id}"
    stack.append(RouteTarget(ranking_route, "ranking", ranking_id))
    if len(parts) == 2:
        return stack
    if len(parts) == 3 and parts[2] == "add":
        return [*stack, RouteTarget(f"{ranking_route}/add", "add_item", ranking_id)]
    if len(parts) == 3 and parts[2] == "compare":
        return [
            *stack,
            RouteTarget(f"{ranking_route}/add", "add_item", ranking_id),
            RouteTarget(f"{ranking_route}/compare", "comparison", ranking_id),
        ]
    return [RouteTarget("/", "home")]
