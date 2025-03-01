# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

# pylint: skip-file

import os

from pytest import fixture
from parameter_store import ParameterStore
from mock import Mock, patch, call
from main import (
    Config,
    ensure_generic_account_can_be_setup,
    update_deployment_account_output_parameters,
)


@fixture
def cls():
    parameter_store = Mock()
    config = Config(
        parameter_store=parameter_store,
        config_path='{0}/stubs/stub_adfconfig.yml'.format(
            os.path.dirname(os.path.realpath(__file__))
        )
    )
    return config


@fixture
def sts():
    sts = Mock()
    sts.assume_cross_account_role.return_value = {
        'Credentials': {
            'AccessKeyId': 'string',
            'SecretAccessKey': 'string',
            'SessionToken': 'string',
            'Expiration': 12345
        },
        'AssumedRoleUser': {
            'AssumedRoleId': 'string',
            'Arn': 'string'
        }
    }
    return sts


def test_ensure_generic_account_can_be_setup(cls, sts):
    assert ensure_generic_account_can_be_setup(sts, cls, '123456789012') == (
        sts.assume_cross_account_role()
    )


def test_update_deployment_account_output_parameters(cls, sts):
    cloudformation = Mock()
    parameter_store = Mock()
    parameter_store.client.put_parameter.return_value = True
    cloudformation.get_stack_regional_outputs.return_value = {
        "kms_arn": 'some_kms_arn',
        "s3_regional_bucket": 'some_s3_bucket'
    }
    with patch.object(ParameterStore, 'put_parameter') as mock:
        expected_calls = [
            call(
                '/cross_region/kms_arn/eu-central-1',
                'some_kms_arn',
            ),
            call(
                '/cross_region/s3_regional_bucket/eu-central-1',
                'some_s3_bucket',
            ),
        ]
        update_deployment_account_output_parameters(
            deployment_account_region='eu-central-1',
            region='eu-central-1',
            deployment_account_role=sts,
            kms_and_bucket_dict={},
            cloudformation=cloudformation
        )
        assert 4 == mock.call_count
        mock.assert_has_calls(expected_calls, any_order=True)
