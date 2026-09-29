from rank_everything.navigation import route_stack


def routes(path: str) -> list[str]:
    return [target.route for target in route_stack(path)]


def test_top_level_routes_keep_home_underneath():
    assert routes("/") == ["/"]
    assert routes("/settings") == ["/", "/settings"]
    assert routes("/rankings/new") == ["/", "/rankings/new"]


def test_ranking_flow_builds_a_real_back_stack():
    assert routes("/rankings/7") == ["/", "/rankings/7"]
    assert routes("/rankings/7/add") == ["/", "/rankings/7", "/rankings/7/add"]
    assert routes("/rankings/7/compare") == [
        "/",
        "/rankings/7",
        "/rankings/7/add",
        "/rankings/7/compare",
    ]


def test_invalid_routes_fall_back_to_home():
    assert routes("/unknown") == ["/"]
    assert routes("/rankings/not-a-number") == ["/"]
    assert routes("/rankings/-1") == ["/"]
    assert routes("/rankings/1/unknown") == ["/"]
