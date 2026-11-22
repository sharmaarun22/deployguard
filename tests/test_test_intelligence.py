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
        {"suite": "checkout", "test_name": "flaky", "status": "passed"},
        {"suite": "checkout", "test_name": "flaky", "status": "failed"},
        {"suite": "checkout", "test_name": "flaky", "status": "passed"},
        {"suite": "catalog", "test_name": "flaky", "status": "passed"},
        {"suite": "catalog", "test_name": "flaky", "status": "passed"},
        {"suite": "catalog", "test_name": "flaky", "status": "passed"},
        {"suite": "checkout", "test_name": "skipped-heavy", "status": "passed"},
        {"suite": "checkout", "test_name": "skipped-heavy", "status": "failed"},
        {"suite": "checkout", "test_name": "skipped-heavy", "status": "skipped"},
        {"suite": "checkout", "test_name": "skipped-heavy", "status": "skipped"},
    ]
    result = flaky_scores(records)
    assert [(item["suite"], item["test_name"]) for item in result] == [("checkout", "flaky")]
    assert result[0]["runs"] == 3
    assert result[0]["failure_rate"] == pytest.approx(1 / 3, abs=0.001)


@pytest.mark.parametrize("duration", ["NaN", "inf", "-0.1"])
def test_junit_rejects_non_finite_or_negative_duration(duration: str) -> None:
    with pytest.raises(ValueError, match="duration"):
        parse_junit_xml(
            f'<testsuite><testcase name="bad" time="{duration}"/></testsuite>'
        )
