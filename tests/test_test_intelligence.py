from xml.etree import ElementTree

import pytest

from backend.app.services.test_intelligence import flaky_scores, parse_junit_xml, parse_robot_xml

JUNIT = """
<testsuite name="suite" tests="3">
  <testcase classname="checkout" name="test_pass" time="0.10"/>
  <testcase classname="checkout" name="test_flaky" time="0.20">
    <failure message="assert 1 == 2"/>
  </testcase>
  <testcase classname="checkout" name="test_flaky" time="0.30"/>
</testsuite>
"""

ROBOT = """
<robot>
  <suite><test name="Login"><status status="PASS" elapsed="1.2"/></test></suite>
</robot>
"""


def test_parse_junit() -> None:
    records = parse_junit_xml(JUNIT)
    assert len(records) == 3
    assert records[1]["status"] == "failed"


def test_malformed_junit() -> None:
    with pytest.raises(ElementTree.ParseError):
        parse_junit_xml("<testsuite>")


def test_parse_robot() -> None:
    records = parse_robot_xml(ROBOT)
    assert records[0]["status"] == "passed"


def test_flaky_requires_mixed_historical_results() -> None:
    records = [
        {"test_name": "flaky", "status": "passed"},
        {"test_name": "flaky", "status": "failed"},
        {"test_name": "flaky", "status": "passed"},
        {"test_name": "stable", "status": "passed"},
        {"test_name": "stable", "status": "passed"},
        {"test_name": "stable", "status": "passed"},
    ]
    result = flaky_scores(records)
    assert [item["test_name"] for item in result] == ["flaky"]
