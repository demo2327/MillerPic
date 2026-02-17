import json
import os

import boto3

secrets = boto3.client("secretsmanager")


def _ensure_stage(secret_id: str, client_request_token: str, stage: str) -> None:
    metadata = secrets.describe_secret(SecretId=secret_id)
    version_ids = metadata.get("VersionIdsToStages", {})
    if client_request_token not in version_ids:
        raise ValueError("Secret version token is not found for this secret")
    if stage not in version_ids[client_request_token]:
        raise ValueError(f"Secret version token is not staged for {stage}")


def _get_current_secret(secret_id: str) -> str:
    response = secrets.get_secret_value(SecretId=secret_id, VersionStage="AWSCURRENT")
    return response["SecretString"]


def handler(event, _context):
    secret_id = event["SecretId"]
    client_request_token = event["ClientRequestToken"]
    step = event["Step"]

    _ensure_stage(secret_id, client_request_token, "AWSPENDING")

    if step == "createSecret":
        try:
            secrets.get_secret_value(
                SecretId=secret_id,
                VersionId=client_request_token,
                VersionStage="AWSPENDING",
            )
        except secrets.exceptions.ResourceNotFoundException:
            current_value = _get_current_secret(secret_id)
            secrets.put_secret_value(
                SecretId=secret_id,
                ClientRequestToken=client_request_token,
                SecretString=current_value,
                VersionStages=["AWSPENDING"],
            )
        return

    if step == "setSecret":
        return

    if step == "testSecret":
        pending = secrets.get_secret_value(
            SecretId=secret_id,
            VersionId=client_request_token,
            VersionStage="AWSPENDING",
        )
        json.loads(pending["SecretString"])
        return

    if step == "finishSecret":
        metadata = secrets.describe_secret(SecretId=secret_id)
        current_version = None
        for version, stages in metadata.get("VersionIdsToStages", {}).items():
            if "AWSCURRENT" in stages:
                current_version = version
                break

        if current_version == client_request_token:
            return

        secrets.update_secret_version_stage(
            SecretId=secret_id,
            VersionStage="AWSCURRENT",
            MoveToVersionId=client_request_token,
            RemoveFromVersionId=current_version,
        )
        return

    raise ValueError(f"Unsupported rotation step: {step}")
