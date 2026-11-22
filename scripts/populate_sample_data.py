from pathlib import Path

from backend.app.db import Base, SessionLocal, engine
from backend.app.models import InfrastructureFinding, Pipeline, TestExecution


def main() -> None:
    Base.metadata.create_all(bind=engine)
    root = Path(__file__).resolve().parents[1]
    workflow = (root / "fixtures" / "workflows" / "failed.yml").read_text(encoding="utf-8")

    with SessionLocal() as db:
        db.query(InfrastructureFinding).delete()
        db.query(TestExecution).delete()
        db.query(Pipeline).delete()
        db.add(
            Pipeline(
                name="sample-ci",
                repository="example/deployguard",
                status="failure",
                source=workflow,
                findings="[]",
            )
        )
        db.add(
            InfrastructureFinding(
                source_type="terraform",
                resource="aws_s3_bucket.public_data",
                rule="public-s3-acl",
                severity="critical",
                description="Synthetic public S3 ACL fixture",
            )
        )
        db.commit()
    print("Sample data populated")


if __name__ == "__main__":
    main()
