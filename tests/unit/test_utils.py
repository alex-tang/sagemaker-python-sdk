# -*- coding: utf-8 -*-

# Copyright 2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
from __future__ import absolute_import

import pytest
from mock import patch

from sagemaker.utils import get_config_value, name_from_base,\
    to_str, DeferredError, extract_name_from_job_arn, secondary_training_status_changed,\
    secondary_training_status_message

from datetime import datetime
import time

NAME = 'base_name'


def test_get_config_value():

    config = {
        'local': {
            'region_name': 'us-west-2',
            'port': '123'
        },
        'other': {
            'key': 1
        }
    }

    assert get_config_value('local.region_name', config) == 'us-west-2'
    assert get_config_value('local', config) == {'region_name': 'us-west-2', 'port': '123'}

    assert get_config_value('does_not.exist', config) is None
    assert get_config_value('other.key', None) is None


def test_deferred_error():
    de = DeferredError(ImportError("pretend the import failed"))
    with pytest.raises(ImportError) as _:  # noqa: F841
        de.something()


def test_bad_import():
    try:
        import pandas_is_not_installed as pd
    except ImportError as e:
        pd = DeferredError(e)
    assert pd is not None
    with pytest.raises(ImportError) as _:  # noqa: F841
        pd.DataFrame()


@patch('sagemaker.utils.sagemaker_timestamp')
def test_name_from_base(sagemaker_timestamp):
    name_from_base(NAME, short=False)
    assert sagemaker_timestamp.called_once


@patch('sagemaker.utils.sagemaker_short_timestamp')
def test_name_from_base_short(sagemaker_short_timestamp):
    name_from_base(NAME, short=True)
    assert sagemaker_short_timestamp.called_once


def test_to_str_with_native_string():
    value = 'some string'
    assert to_str(value) == value


def test_to_str_with_unicode_string():
    value = u'åñøthér strîng'
    assert to_str(value) == value


def test_name_from_tuning_arn():
    arn = 'arn:aws:sagemaker:us-west-2:968277160000:hyper-parameter-tuning-job/resnet-sgd-tuningjob-11-07-34-11'
    name = extract_name_from_job_arn(arn)
    assert name == 'resnet-sgd-tuningjob-11-07-34-11'


def test_name_from_training_arn():
    arn = 'arn:aws:sagemaker:us-west-2:968277160000:training-job/resnet-sgd-tuningjob-11-22-38-46-002-2927640b'
    name = extract_name_from_job_arn(arn)
    assert name == 'resnet-sgd-tuningjob-11-22-38-46-002-2927640b'


MESSAGE = 'message'
STATUS = 'status'
TRAINING_JOB_DESCRIPTION_1 = {
    'SecondaryStatusTransitions': [{'StatusMessage': MESSAGE, 'Status': STATUS}]
}
TRAINING_JOB_DESCRIPTION_2 = {
    'SecondaryStatusTransitions': [{'StatusMessage': 'different message', 'Status': STATUS}]
}

TRAINING_JOB_DESCRIPTION_EMPTY = {
    'SecondaryStatusTransitions': []
}


def test_secondary_training_status_changed_true():
    changed = secondary_training_status_changed(TRAINING_JOB_DESCRIPTION_1, TRAINING_JOB_DESCRIPTION_2)
    assert changed is True


def test_secondary_training_status_changed_false():
    changed = secondary_training_status_changed(TRAINING_JOB_DESCRIPTION_1, TRAINING_JOB_DESCRIPTION_1)
    assert changed is False


def test_secondary_training_status_changed_prev_missing():
    changed = secondary_training_status_changed(TRAINING_JOB_DESCRIPTION_1, {})
    assert changed is True


def test_secondary_training_status_changed_prev_none():
    changed = secondary_training_status_changed(TRAINING_JOB_DESCRIPTION_1, None)
    assert changed is True


def test_secondary_training_status_changed_current_missing():
    changed = secondary_training_status_changed({}, TRAINING_JOB_DESCRIPTION_1)
    assert changed is False


def test_secondary_training_status_changed_empty():
    changed = secondary_training_status_changed(TRAINING_JOB_DESCRIPTION_EMPTY, TRAINING_JOB_DESCRIPTION_1)
    assert changed is False


def test_secondary_training_status_message_status_changed():
    now = datetime.now()
    TRAINING_JOB_DESCRIPTION_1['SecondaryStatusTransitions'][-1]['StartTime'] = now
    expected = '{} {} - {}'.format(
        datetime.utcfromtimestamp(time.mktime(now.timetuple())).strftime('%Y-%m-%d %H:%M:%S'),
        STATUS,
        MESSAGE
    )
    assert secondary_training_status_message(TRAINING_JOB_DESCRIPTION_1, TRAINING_JOB_DESCRIPTION_EMPTY) == expected


def test_secondary_training_status_message_status_not_changed():
    now = datetime.now()
    TRAINING_JOB_DESCRIPTION_1['SecondaryStatusTransitions'][-1]['StartTime'] = now
    assert secondary_training_status_message(TRAINING_JOB_DESCRIPTION_1, TRAINING_JOB_DESCRIPTION_2) == MESSAGE
