"""Tests for list_session_groups."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import tensorflow as tf

from tensorboard.backend.event_processing import plugin_event_multiplexer
from tensorboard.backend.event_processing import event_accumulator
from tensorboard.plugins.hparams import api_pb2
from tensorboard.plugins.hparams import backend_context
from tensorboard.plugins.hparams import list_session_groups
from tensorboard.plugins.hparams import metadata
from tensorboard.plugins.hparams import plugin_data_pb2
from google.protobuf import text_format

DATA_TYPE_EXPERIMENT = metadata.DATA_TYPE_EXPERIMENT
DATA_TYPE_SESSION_START_INFO = metadata.DATA_TYPE_SESSION_START_INFO
DATA_TYPE_SESSION_END_INFO = metadata.DATA_TYPE_SESSION_END_INFO

TensorEvent = event_accumulator.TensorEvent

class ListSessionGroupsTest(tf.test.TestCase):

  def setUp(self):
    self._mock_multiplexer = tf.test.mock.create_autospec(
        plugin_event_multiplexer.EventMultiplexer)
    self._mock_multiplexer.PluginRunToTagToContent.return_value = {
        '' : {
            metadata.EXPERIMENT_TAG :
            self._serialized_plugin_data(
                DATA_TYPE_EXPERIMENT, '''
                  description: 'Test experiment'
                  user: 'Test user'
                  hparam_infos: [
                    {
                      name: 'initial_temp'
                      type: DATA_TYPE_FLOAT64
                    },
                    {
                      name: 'final_temp'
                      type: DATA_TYPE_FLOAT64
                    },
                    { name: 'string_hparam' },
                    { name: 'bool_hparam' },
                    { name: 'optional_string_hparam' }
                  ]
                  metric_infos: [
                    { name: { tag: 'current_temp' } },
                    { name: { tag: 'delta_temp' } },
                    { name: { tag: 'optional_metric' } }
                  ]
                  ''')
        },
        'session_1' : {
            metadata.SESSION_START_INFO_TAG :
            self._serialized_plugin_data(
                DATA_TYPE_SESSION_START_INFO, '''
                  hparams:{ key: 'initial_temp' value: { number_value: 270 } },
                  hparams:{ key: 'final_temp' value: { number_value: 150 } },
                  hparams:{
                    key: 'string_hparam' value: { string_value: 'a string' }
                  },
                  hparams:{ key: 'bool_hparam' value: { bool_value: true } }
                  group_name: 'group_1'
                  start_time_secs: 314159
                '''),
            metadata.SESSION_END_INFO_TAG :
            self._serialized_plugin_data(
                DATA_TYPE_SESSION_END_INFO, '''
                  status: STATUS_SUCCESS
                  end_time_secs: 314164
                ''')
        },
       'session_2' : {
            metadata.SESSION_START_INFO_TAG :
            self._serialized_plugin_data(
                DATA_TYPE_SESSION_START_INFO, '''
                  hparams:{ key: 'initial_temp' value: { number_value: 280 } },
                  hparams:{ key: 'final_temp' value: { number_value: 100 } },
                  hparams:{
                    key: 'string_hparam' value: { string_value: 'AAAAA' }
                  },
                  hparams:{ key: 'bool_hparam' value: { bool_value: false } }
                  group_name: 'group_2'
                  start_time_secs: 314159
                '''),
            metadata.SESSION_END_INFO_TAG :
            self._serialized_plugin_data(
                DATA_TYPE_SESSION_END_INFO, '''
                   status: STATUS_SUCCESS
                   end_time_secs: 314164
                ''')
        },
       'session_3' : {
            metadata.SESSION_START_INFO_TAG :
            self._serialized_plugin_data(
                DATA_TYPE_SESSION_START_INFO, '''
                  hparams:{ key: 'initial_temp' value: { number_value: 280 } },
                  hparams:{ key: 'final_temp' value: { number_value: 100 } },
                  hparams:{
                    key: 'string_hparam' value: { string_value: 'AAAAA' }
                  },
                  hparams:{ key: 'bool_hparam' value: { bool_value: false } }
                  group_name: 'group_2'
                  start_time_secs: 314159
                '''),
            metadata.SESSION_END_INFO_TAG :
            self._serialized_plugin_data(
                DATA_TYPE_SESSION_END_INFO, '''
                  status: STATUS_SUCCESS
                  end_time_secs: 314164
                ''')
        },
       'session_4' : {
            metadata.SESSION_START_INFO_TAG :
            self._serialized_plugin_data(
                DATA_TYPE_SESSION_START_INFO, '''
                  hparams:{ key: 'initial_temp' value: { number_value: 300 } },
                  hparams:{ key: 'final_temp' value: { number_value: 120 } },
                  hparams:{
                    key: 'string_hparam' value: { string_value: 'a string_3' }
                  },
                  hparams:{ key: 'bool_hparam' value: { bool_value: true } }
                  hparams:{
                    key: 'optional_string_hparam' value { string_value: 'BB' }
                  },
                  group_name: 'group_3'
                  start_time_secs: 314159
                '''),
            metadata.SESSION_END_INFO_TAG :
            self._serialized_plugin_data(
                DATA_TYPE_SESSION_END_INFO, '''
                  status: STATUS_SUCCESS
                  end_time_secs: 314164
                ''')
        },
    }
    self._mock_multiplexer.Tensors.side_effect = self._mock_tensors

  # A mock version of EventMultiplexer.Tensors
  def _mock_tensors(self, run, tag):
    result_dict = {
      'session_1': {
        'current_temp': [
            TensorEvent(
                wall_time=1, step=1, tensor_proto=tf.make_tensor_proto(10.0))
        ],
        'delta_temp': [
            TensorEvent(
                wall_time=1, step=1, tensor_proto=tf.make_tensor_proto(20.0)),
            TensorEvent(
                wall_time=10, step=2, tensor_proto=tf.make_tensor_proto(15.0))
        ],
        'optional_metric' : [
            TensorEvent(
                wall_time=1, step=1, tensor_proto=tf.make_tensor_proto(20.0)),
            TensorEvent(
                wall_time=2, step=20, tensor_proto=tf.make_tensor_proto(33.0))
        ]
      },
      'session_2': {
        'current_temp': [
            TensorEvent(
                wall_time=1, step=1, tensor_proto=tf.make_tensor_proto(100.0)),
        ],
        'delta_temp': [
            TensorEvent(
                wall_time=1, step=1, tensor_proto=tf.make_tensor_proto(200.0)),
            TensorEvent(
                wall_time=10, step=2, tensor_proto=tf.make_tensor_proto(150.0))
        ]
      },
      'session_3': {
        'current_temp': [
            TensorEvent(
                wall_time=1, step=1, tensor_proto=tf.make_tensor_proto(1.0)),
        ],
        'delta_temp': [
            TensorEvent(
                wall_time=1, step=1, tensor_proto=tf.make_tensor_proto(2.0)),
            TensorEvent(
                wall_time=10, step=2, tensor_proto=tf.make_tensor_proto(1.5))
        ]
      },
      'session_4': {
        'current_temp': [
            TensorEvent(
                wall_time=1, step=1, tensor_proto=tf.make_tensor_proto(101.0)),
        ],
        'delta_temp': [
            TensorEvent(
                wall_time=1, step=1, tensor_proto=tf.make_tensor_proto(201.0)),
            TensorEvent(
                wall_time=10, step=2, tensor_proto=tf.make_tensor_proto(-151.0))
        ]
      },
    }
    return result_dict[run][tag]

  def test_empty_request(self):
    self._verify_handler(
        request='',
        expected_response='''
          session_groups {
            name: "group_1"
            hparams { key: "bool_hparam" value { bool_value: true } }
            hparams { key: "final_temp" value { number_value: 150.0 } }
            hparams { key: "initial_temp" value { number_value: 270.0 } }
            hparams { key: "string_hparam" value { string_value: "a string" } }
            metric_values {
              name { tag: "current_temp" }
              value: 10
              training_step: 1
              wall_time_secs: 1.0
            }
            metric_values { name { tag: "delta_temp" } value: 15
              training_step: 2
              wall_time_secs: 10.0
            }
            metric_values { name { tag: "optional_metric" } value: 33
              training_step: 20
              wall_time_secs: 2.0
            }
            sessions {
              name: "session_1"
              start_time_secs: 314159
              end_time_secs: 314164
              status: STATUS_SUCCESS
              metric_values {
                name { tag: "current_temp" }
                value: 10
                training_step: 1
                wall_time_secs: 1.0
              }
              metric_values { name { tag: "delta_temp" } value: 15
                training_step: 2
                wall_time_secs: 10.0
              }

              metric_values { name { tag: "optional_metric" } value: 33
                training_step: 20
                wall_time_secs: 2.0
              }
            }
          }
          session_groups {
            name: "group_2"
            hparams { key: "bool_hparam" value { bool_value: false } }
            hparams { key: "final_temp" value { number_value: 100.0 } }
            hparams { key: "initial_temp" value { number_value: 280.0 } }
            hparams { key: "string_hparam" value { string_value: "AAAAA"}}
            metric_values {
              name { tag: "current_temp" }
              value: 100
              training_step: 1
              wall_time_secs: 1.0
            }
            metric_values { name { tag: "delta_temp" } value: 150
              training_step: 2
              wall_time_secs: 10.0
            }
            sessions {
              name: "session_2"
              start_time_secs: 314159
              end_time_secs: 314164
              status: STATUS_SUCCESS
              metric_values {
                name { tag: "current_temp" }
                value: 100
                training_step: 1
                wall_time_secs: 1.0
              }
              metric_values { name { tag: "delta_temp" } value: 150
                training_step: 2
                wall_time_secs: 10.0
              }
            }
            sessions {
              name: "session_3"
              start_time_secs: 314159
              end_time_secs: 314164
              status: STATUS_SUCCESS
              metric_values {
                name { tag: "current_temp" }
                value: 1.0
                training_step: 1
                wall_time_secs: 1.0
              }
              metric_values { name { tag: "delta_temp" } value: 1.5
                training_step: 2
                wall_time_secs: 10.0
              }
            }
          }
          session_groups {
            name: "group_3"
            hparams { key: "bool_hparam" value { bool_value: true } }
            hparams { key: "final_temp" value { number_value: 120.0 } }
            hparams { key: "initial_temp" value { number_value: 300.0 } }
            hparams { key: "string_hparam" value { string_value: "a string_3"}}
            hparams {
              key: 'optional_string_hparam' value { string_value: 'BB' }
            }
            metric_values {
              name { tag: "current_temp" }
              value: 101.0
              training_step: 1
              wall_time_secs: 1.0
            }
            metric_values { name { tag: "delta_temp" } value: -151.0
              training_step: 2
              wall_time_secs: 10.0
            }
            sessions {
              name: "session_4"
              start_time_secs: 314159
              end_time_secs: 314164
              status: STATUS_SUCCESS
              metric_values {
                name { tag: "current_temp" }
                value: 101.0
                training_step: 1
                wall_time_secs: 1.0
              }
              metric_values { name { tag: "delta_temp" } value: -151.0
                training_step: 2
                wall_time_secs: 10.0
              }
            }
          }
          total_size: 3
        ''')

  def test_filter_regexp(self):
    self._verify_handler(
        request='''
          col_params: {
            hparam: 'string_hparam'
            regexp: 'AA*'
          }
        ''',
        expected_response='''
          session_groups {
            name: "group_2"
            hparams { key: "bool_hparam" value { bool_value: false } }
            hparams { key: "final_temp" value { number_value: 100.0 } }
            hparams { key: "initial_temp" value { number_value: 280.0 } }
            hparams { key: "string_hparam" value { string_value: "AAAAA"}}
            metric_values {
              name { tag: "current_temp" } value: 100
              training_step: 1
              wall_time_secs: 1.0
            }
            metric_values {
              name { tag: "delta_temp" }
              value: 150
              training_step: 2
              wall_time_secs: 10.0
            }
            sessions {
              name: "session_2"
              start_time_secs: 314159
              end_time_secs: 314164
              status: STATUS_SUCCESS
              metric_values { name { tag: "current_temp" } value: 100
                training_step: 1
                wall_time_secs: 1.0
              }
              metric_values { name { tag: "delta_temp" } value: 150
                training_step: 2
                wall_time_secs: 10.0
              }
            }
            sessions {
              name: "session_3"
              start_time_secs: 314159
              end_time_secs: 314164
              status: STATUS_SUCCESS
              metric_values { name { tag: "current_temp" } value: 1.0
                training_step: 1
                wall_time_secs: 1.0
              }
              metric_values { name { tag: "delta_temp" } value: 1.5
                training_step: 2
                wall_time_secs: 10.0
              }
            }
          }
          total_size: 1
        ''')
    # Test filtering out all session groups.
    self._verify_handler(
        request='''
          col_params: {
            hparam: 'string_hparam'
            regexp: 'a string_100'
          }
        ''',
        expected_response='total_size: 0')

  def test_filter_interval(self):
    self._verify_handler(
        request='''
          col_params: {
            hparam: 'initial_temp'
            interval: { min_value: 270 max_value: 282 }
          }
        ''',
        expected_response='''
          session_groups {
            name: "group_1"
            hparams { key: "bool_hparam" value { bool_value: true } }
            hparams { key: "final_temp" value { number_value: 150.0 } }
            hparams { key: "initial_temp" value { number_value: 270.0 } }
            hparams { key: "string_hparam" value { string_value: "a string" } }
            metric_values { name { tag: "current_temp" } value: 10
              training_step: 1
              wall_time_secs: 1.0
            }
            metric_values { name { tag: "delta_temp" } value: 15
              training_step: 2
              wall_time_secs: 10.0
            }
            metric_values { name { tag: "optional_metric" } value: 33
              training_step: 20
              wall_time_secs: 2.0
            }
            sessions {
              name: "session_1"
              start_time_secs: 314159
              end_time_secs: 314164
              status: STATUS_SUCCESS
              metric_values { name { tag: "current_temp" } value: 10
                training_step: 1
                wall_time_secs: 1.0
              }
              metric_values { name { tag: "delta_temp" } value: 15
                training_step: 2
                wall_time_secs: 10.0
              }
              metric_values { name { tag: "optional_metric" } value: 33
                training_step: 20
                wall_time_secs: 2.0
              }
            }
          }
          session_groups {
            name: "group_2"
            hparams { key: "bool_hparam" value { bool_value: false } }
            hparams { key: "final_temp" value { number_value: 100.0 } }
            hparams { key: "initial_temp" value { number_value: 280.0 } }
            hparams { key: "string_hparam" value { string_value: "AAAAA"}}
            metric_values { name { tag: "current_temp" } value: 100
              training_step: 1
              wall_time_secs: 1.0
            }
            metric_values { name { tag: "delta_temp" } value: 150
              training_step: 2
              wall_time_secs: 10.0
            }
            sessions {
              name: "session_2"
              start_time_secs: 314159
              end_time_secs: 314164
              status: STATUS_SUCCESS
              metric_values { name { tag: "current_temp" } value: 100
                training_step: 1
                wall_time_secs: 1.0
              }
              metric_values { name { tag: "delta_temp" } value: 150
                training_step: 2
                wall_time_secs: 10.0
              }
            }
            sessions {
              name: "session_3"
              start_time_secs: 314159
              end_time_secs: 314164
              status: STATUS_SUCCESS
              metric_values { name { tag: "current_temp" } value: 1.0
                training_step: 1
                wall_time_secs: 1.0
              }
              metric_values { name { tag: "delta_temp" } value: 1.5
                training_step: 2
                wall_time_secs: 10.0
              }
            }
          }
          total_size: 2
        ''')

  def test_filter_discrete_set(self):
    self._verify_handler(
        request='''
          col_params: {
            metric: { tag: 'current_temp' }
            discrete_set: { values: [{ number_value: 101.0 },
                                     { number_value: 10.0 }] }
          }
        ''',
        expected_response='''
          session_groups {
            name: "group_1"
            hparams { key: "bool_hparam" value { bool_value: true } }
            hparams { key: "final_temp" value { number_value: 150.0 } }
            hparams { key: "initial_temp" value { number_value: 270.0 } }
            hparams { key: "string_hparam" value { string_value: "a string" } }
            metric_values { name { tag: "current_temp" } value: 10
              training_step: 1
              wall_time_secs: 1.0
            }
            metric_values { name { tag: "delta_temp" } value: 15
              training_step: 2
              wall_time_secs: 10.0
            }
            metric_values { name { tag: "optional_metric" } value: 33
              training_step: 20
              wall_time_secs: 2.0
            }
            sessions {
              name: "session_1"
              start_time_secs: 314159
              end_time_secs: 314164
              status: STATUS_SUCCESS
              metric_values { name { tag: "current_temp" } value: 10
                training_step: 1
                wall_time_secs: 1.0
              }
              metric_values { name { tag: "delta_temp" } value: 15
                training_step: 2
                wall_time_secs: 10.0
              }
              metric_values { name { tag: "optional_metric" } value: 33
                training_step: 20
                wall_time_secs: 2.0
              }
            }
          }
          session_groups {
            name: "group_3"
            hparams { key: "bool_hparam" value { bool_value: true } }
            hparams { key: "final_temp" value { number_value: 120.0 } }
            hparams { key: "initial_temp" value { number_value: 300.0 } }
            hparams { key: "string_hparam" value { string_value: "a string_3"}}
            hparams {
              key: 'optional_string_hparam' value { string_value: 'BB' }
            }
            metric_values { name { tag: "current_temp" } value: 101.0
              training_step: 1
              wall_time_secs: 1.0
            }
            metric_values { name { tag: "delta_temp" } value: -151.0
              training_step: 2
              wall_time_secs: 10.0
            }
            sessions {
              name: "session_4"
              start_time_secs: 314159
              end_time_secs: 314164
              status: STATUS_SUCCESS
              metric_values { name { tag: "current_temp" } value: 101.0
                training_step: 1
                wall_time_secs: 1.0
              }
              metric_values { name { tag: "delta_temp" } value: -151.0
                training_step: 2
                wall_time_secs: 10.0
              }
            }
          }
          total_size: 2
        ''')

  def test_filter_multiple_columns(self):
    self._verify_handler(
        request='''
          col_params: {
            metric: { tag: 'current_temp' }
            discrete_set: { values: [{ number_value: 101.0 },
                                     { number_value: 10.0 }] }
          }
          col_params: {
            hparam: 'initial_temp'
            interval: { min_value: 270 max_value: 282 }
          }
        ''',
        expected_response='''
          session_groups {
            name: "group_1"
            hparams { key: "bool_hparam" value { bool_value: true } }
            hparams { key: "final_temp" value { number_value: 150.0 } }
            hparams { key: "initial_temp" value { number_value: 270.0 } }
            hparams { key: "string_hparam" value { string_value: "a string" } }
            metric_values { name { tag: "current_temp" } value: 10
              training_step: 1
              wall_time_secs: 1.0
            }
            metric_values { name { tag: "delta_temp" } value: 15
              training_step: 2
              wall_time_secs: 10.0
            }
            metric_values { name { tag: "optional_metric" } value: 33
              training_step: 20
              wall_time_secs: 2.0
            }
            sessions {
              name: "session_1"
              start_time_secs: 314159
              end_time_secs: 314164
              status: STATUS_SUCCESS
              metric_values { name { tag: "current_temp" } value: 10
                training_step: 1
                wall_time_secs: 1.0
              }
              metric_values { name { tag: "delta_temp" } value: 15
                training_step: 2
                wall_time_secs: 10.0
              }
              metric_values { name { tag: "optional_metric" } value: 33
                training_step: 20
                wall_time_secs: 2.0
              }
            }
          }
          total_size: 1
        ''')

  def test_filter_single_column_with_missing_values(self):
    self._verify_handler(
        request='''
          col_params: {
            hparam: 'optional_string_hparam'
            regexp: 'B*'
          }
        ''',
        expected_response='''
          session_groups {
            name: "group_3"
            hparams { key: "bool_hparam" value { bool_value: true } }
            hparams { key: "final_temp" value { number_value: 120.0 } }
            hparams { key: "initial_temp" value { number_value: 300.0 } }
            hparams { key: "string_hparam" value { string_value: "a string_3"}}
            hparams {
              key: 'optional_string_hparam' value { string_value: 'BB' }
            }
            metric_values { name { tag: "current_temp" } value: 101.0
              training_step: 1
              wall_time_secs: 1.0
            }
            metric_values { name { tag: "delta_temp" } value: -151.0
              training_step: 2
              wall_time_secs: 10.0
            }
            sessions {
              name: "session_4"
              start_time_secs: 314159
              end_time_secs: 314164
              status: STATUS_SUCCESS
              metric_values { name { tag: "current_temp" } value: 101.0
                training_step: 1
                wall_time_secs: 1.0
              }
              metric_values { name { tag: "delta_temp" } value: -151.0
                training_step: 2
                wall_time_secs: 10.0
              }
            }
          }
          total_size: 1
        ''')
    self._verify_handler(
        request='''
          col_params: {
            metric: { tag: 'optional_metric' }
            discrete_set: { values: { number_value: 33.0 } }
          }
        ''',
        expected_response='''
          session_groups {
            name: "group_1"
            hparams { key: "bool_hparam" value { bool_value: true } }
            hparams { key: "final_temp" value { number_value: 150.0 } }
            hparams { key: "initial_temp" value { number_value: 270.0 } }
            hparams { key: "string_hparam" value { string_value: "a string" } }
            metric_values { name { tag: "current_temp" } value: 10
              training_step: 1
              wall_time_secs: 1.0
            }
            metric_values { name { tag: "delta_temp" } value: 15
              training_step: 2
              wall_time_secs: 10.0
            }
            metric_values { name { tag: "optional_metric" } value: 33
              training_step: 20
              wall_time_secs: 2.0
            }
            sessions {
              name: "session_1"
              start_time_secs: 314159
              end_time_secs: 314164
              status: STATUS_SUCCESS
              metric_values { name { tag: "current_temp" } value: 10
                training_step: 1
                wall_time_secs: 1.0
              }
              metric_values { name { tag: "delta_temp" } value: 15
                training_step: 2
                wall_time_secs: 10.0
              }
              metric_values { name { tag: "optional_metric" } value: 33
                training_step: 20
                wall_time_secs: 2.0
              }
            }
          }
          total_size: 1
        ''')

  def test_sort_one_column(self):
    self._verify_handler(
        request='''
          col_params: {
            metric: { tag: 'delta_temp' }
            order: ORDER_ASC
          }
        ''',
        expected_response='''
          session_groups {
            name: "group_3"
            hparams { key: "bool_hparam" value { bool_value: true } }
            hparams { key: "final_temp" value { number_value: 120.0 } }
            hparams { key: "initial_temp" value { number_value: 300.0 } }
            hparams { key: "string_hparam" value { string_value: "a string_3"}}
            hparams {
              key: 'optional_string_hparam' value { string_value: 'BB' }
            }
            metric_values { name { tag: "current_temp" } value: 101.0
              training_step: 1
              wall_time_secs: 1.0
            }
            metric_values { name { tag: "delta_temp" } value: -151.0
              training_step: 2
              wall_time_secs: 10.0
            }
            sessions {
              name: "session_4"
              start_time_secs: 314159
              end_time_secs: 314164
              status: STATUS_SUCCESS
              metric_values { name { tag: "current_temp" } value: 101.0
                training_step: 1
                wall_time_secs: 1.0
              }
              metric_values { name { tag: "delta_temp" } value: -151.0
                training_step: 2
                wall_time_secs: 10.0
              }
            }
          }
          session_groups {
            name: "group_1"
            hparams { key: "bool_hparam" value { bool_value: true } }
            hparams { key: "final_temp" value { number_value: 150.0 } }
            hparams { key: "initial_temp" value { number_value: 270.0 } }
            hparams { key: "string_hparam" value { string_value: "a string" } }
            metric_values { name { tag: "current_temp" } value: 10
              training_step: 1
              wall_time_secs: 1.0
            }
            metric_values { name { tag: "delta_temp" } value: 15
              training_step: 2
              wall_time_secs: 10.0
            }
            metric_values { name { tag: "optional_metric" } value: 33
              training_step: 20
              wall_time_secs: 2.0
            }
            sessions {
              name: "session_1"
              start_time_secs: 314159
              end_time_secs: 314164
              status: STATUS_SUCCESS
              metric_values { name { tag: "current_temp" } value: 10
                training_step: 1
                wall_time_secs: 1.0
              }
              metric_values { name { tag: "delta_temp" } value: 15
                training_step: 2
                wall_time_secs: 10.0
              }
              metric_values { name { tag: "optional_metric" } value: 33
                training_step: 20
                wall_time_secs: 2.0
              }
            }
          }
          session_groups {
            name: "group_2"
            hparams { key: "bool_hparam" value { bool_value: false } }
            hparams { key: "final_temp" value { number_value: 100.0 } }
            hparams { key: "initial_temp" value { number_value: 280.0 } }
            hparams { key: "string_hparam" value { string_value: "AAAAA"}}
            metric_values { name { tag: "current_temp" } value: 100
              training_step: 1
              wall_time_secs: 1.0
            }
            metric_values { name { tag: "delta_temp" } value: 150
              training_step: 2
              wall_time_secs: 10.0
            }
            sessions {
              name: "session_2"
              start_time_secs: 314159
              end_time_secs: 314164
              status: STATUS_SUCCESS
              metric_values { name { tag: "current_temp" } value: 100
                training_step: 1
                wall_time_secs: 1.0
              }
              metric_values { name { tag: "delta_temp" } value: 150
                training_step: 2
                wall_time_secs: 10.0
              }
            }
            sessions {
              name: "session_3"
              start_time_secs: 314159
              end_time_secs: 314164
              status: STATUS_SUCCESS
              metric_values { name { tag: "current_temp" } value: 1.0
                training_step: 1
                wall_time_secs: 1.0
              }
              metric_values { name { tag: "delta_temp" } value: 1.5
                training_step: 2
                wall_time_secs: 10.0
              }
            }
          }
          total_size: 3
        ''')
    self._verify_handler(
        request='''
          col_params: {
            hparam: 'string_hparam'
            order: ORDER_ASC
          }
        ''',
        expected_response='''
          session_groups {
            name: "group_2"
            hparams { key: "bool_hparam" value { bool_value: false } }
            hparams { key: "final_temp" value { number_value: 100.0 } }
            hparams { key: "initial_temp" value { number_value: 280.0 } }
            hparams { key: "string_hparam" value { string_value: "AAAAA"}}
            metric_values { name { tag: "current_temp" } value: 100
              training_step: 1
              wall_time_secs: 1.0
            }
            metric_values { name { tag: "delta_temp" } value: 150
              training_step: 2
              wall_time_secs: 10.0
            }
            sessions {
              name: "session_2"
              start_time_secs: 314159
              end_time_secs: 314164
              status: STATUS_SUCCESS
              metric_values { name { tag: "current_temp" } value: 100
                training_step: 1
                wall_time_secs: 1.0
              }
              metric_values { name { tag: "delta_temp" } value: 150
                training_step: 2
                wall_time_secs: 10.0
              }
            }
            sessions {
              name: "session_3"
              start_time_secs: 314159
              end_time_secs: 314164
              status: STATUS_SUCCESS
              metric_values { name { tag: "current_temp" } value: 1.0
                training_step: 1
                wall_time_secs: 1.0
              }
              metric_values { name { tag: "delta_temp" } value: 1.5
                training_step: 2
                wall_time_secs: 10.0
              }
            }
          }
          session_groups {
            name: "group_1"
            hparams { key: "bool_hparam" value { bool_value: true } }
            hparams { key: "final_temp" value { number_value: 150.0 } }
            hparams { key: "initial_temp" value { number_value: 270.0 } }
            hparams { key: "string_hparam" value { string_value: "a string" } }
            metric_values { name { tag: "current_temp" } value: 10
              training_step: 1
              wall_time_secs: 1.0
            }
            metric_values { name { tag: "delta_temp" } value: 15
              training_step: 2
              wall_time_secs: 10.0
            }
            metric_values { name { tag: "optional_metric" } value: 33
              training_step: 20
              wall_time_secs: 2.0
            }
            sessions {
              name: "session_1"
              start_time_secs: 314159
              end_time_secs: 314164
              status: STATUS_SUCCESS
              metric_values { name { tag: "current_temp" } value: 10
                training_step: 1
                wall_time_secs: 1.0
              }
              metric_values { name { tag: "delta_temp" } value: 15
                training_step: 2
                wall_time_secs: 10.0
              }
              metric_values { name { tag: "optional_metric" } value: 33
                training_step: 20
                wall_time_secs: 2.0
            }
            }
          }
          session_groups {
            name: "group_3"
            hparams { key: "bool_hparam" value { bool_value: true } }
            hparams { key: "final_temp" value { number_value: 120.0 } }
            hparams { key: "initial_temp" value { number_value: 300.0 } }
            hparams { key: "string_hparam" value { string_value: "a string_3"}}
            hparams {
              key: 'optional_string_hparam' value { string_value: 'BB' }
            }
            metric_values { name { tag: "current_temp" } value: 101.0
              training_step: 1
              wall_time_secs: 1.0
            }
            metric_values { name { tag: "delta_temp" } value: -151.0
              training_step: 2
              wall_time_secs: 10.0
            }
            sessions {
              name: "session_4"
              start_time_secs: 314159
              end_time_secs: 314164
              status: STATUS_SUCCESS
              metric_values { name { tag: "current_temp" } value: 101.0
                training_step: 1
                wall_time_secs: 1.0
              }
              metric_values { name { tag: "delta_temp" } value: -151.0
                training_step: 2
                wall_time_secs: 10.0
              }
            }
          }
          total_size: 3
        ''')
    # Test descending order.
    self._verify_handler(
        request='''
          col_params: {
            hparam: 'string_hparam'
            order: ORDER_DESC
          }
        ''',
        expected_response='''
          session_groups {
            name: "group_3"
            hparams { key: "bool_hparam" value { bool_value: true } }
            hparams { key: "final_temp" value { number_value: 120.0 } }
            hparams { key: "initial_temp" value { number_value: 300.0 } }
            hparams { key: "string_hparam" value { string_value: "a string_3"}}
            hparams {
              key: 'optional_string_hparam' value { string_value: 'BB' }
            }
            metric_values { name { tag: "current_temp" } value: 101.0
              training_step: 1
              wall_time_secs: 1.0
            }
            metric_values { name { tag: "delta_temp" } value: -151.0
              training_step: 2
              wall_time_secs: 10.0
            }
            sessions {
              name: "session_4"
              start_time_secs: 314159
              end_time_secs: 314164
              status: STATUS_SUCCESS
              metric_values { name { tag: "current_temp" } value: 101.0
                training_step: 1
                wall_time_secs: 1.0
              }
              metric_values { name { tag: "delta_temp" } value: -151.0
                training_step: 2
                wall_time_secs: 10.0
              }
            }
          }
          session_groups {
            name: "group_1"
            hparams { key: "bool_hparam" value { bool_value: true } }
            hparams { key: "final_temp" value { number_value: 150.0 } }
            hparams { key: "initial_temp" value { number_value: 270.0 } }
            hparams { key: "string_hparam" value { string_value: "a string" } }
            metric_values { name { tag: "current_temp" } value: 10
              training_step: 1
              wall_time_secs: 1.0
            }
            metric_values { name { tag: "delta_temp" } value: 15
              training_step: 2
              wall_time_secs: 10.0
            }
            metric_values { name { tag: "optional_metric" } value: 33
              training_step: 20
              wall_time_secs: 2.0
            }
            sessions {
              name: "session_1"
              start_time_secs: 314159
              end_time_secs: 314164
              status: STATUS_SUCCESS
              metric_values { name { tag: "current_temp" } value: 10
                training_step: 1
                wall_time_secs: 1.0
              }
              metric_values { name { tag: "delta_temp" } value: 15
                training_step: 2
                wall_time_secs: 10.0
              }
              metric_values { name { tag: "optional_metric" } value: 33
                training_step: 20
                wall_time_secs: 2.0
            }
            }
          }
          total_size: 3
          session_groups {
            name: "group_2"
            hparams { key: "bool_hparam" value { bool_value: false } }
            hparams { key: "final_temp" value { number_value: 100.0 } }
            hparams { key: "initial_temp" value { number_value: 280.0 } }
            hparams { key: "string_hparam" value { string_value: "AAAAA"}}
            metric_values { name { tag: "current_temp" } value: 100
              training_step: 1
              wall_time_secs: 1.0
            }
            metric_values { name { tag: "delta_temp" } value: 150
              training_step: 2
              wall_time_secs: 10.0
            }
            sessions {
              name: "session_2"
              start_time_secs: 314159
              end_time_secs: 314164
              status: STATUS_SUCCESS
              metric_values { name { tag: "current_temp" } value: 100
                training_step: 1
                wall_time_secs: 1.0
              }
              metric_values { name { tag: "delta_temp" } value: 150
                training_step: 2
                wall_time_secs: 10.0
              }
            }
            sessions {
              name: "session_3"
              start_time_secs: 314159
              end_time_secs: 314164
              status: STATUS_SUCCESS
              metric_values { name { tag: "current_temp" } value: 1.0
                training_step: 1
                wall_time_secs: 1.0
              }
              metric_values { name { tag: "delta_temp" } value: 1.5
                training_step: 2
                wall_time_secs: 10.0
              }
            }
          }
        ''')

  def test_sort_multiple_columns(self):
    self._verify_handler(
        request='''
          col_params: {
            hparam: 'bool_hparam'
            order: ORDER_ASC
          }
          col_params: {
            metric: { tag: 'delta_temp' }
            order: ORDER_ASC
          }
        ''',
        expected_response='''
          session_groups {
            name: "group_2"
            hparams { key: "bool_hparam" value { bool_value: false } }
            hparams { key: "final_temp" value { number_value: 100.0 } }
            hparams { key: "initial_temp" value { number_value: 280.0 } }
            hparams { key: "string_hparam" value { string_value: "AAAAA"}}
            metric_values { name { tag: "current_temp" } value: 100
              training_step: 1
              wall_time_secs: 1.0
            }
            metric_values { name { tag: "delta_temp" } value: 150
              training_step: 2
              wall_time_secs: 10.0
            }
            sessions {
              name: "session_2"
              start_time_secs: 314159
              end_time_secs: 314164
              status: STATUS_SUCCESS
              metric_values { name { tag: "current_temp" } value: 100
                training_step: 1
                wall_time_secs: 1.0
              }
              metric_values { name { tag: "delta_temp" } value: 150
                training_step: 2
                wall_time_secs: 10.0
              }
            }
            sessions {
              name: "session_3"
              start_time_secs: 314159
              end_time_secs: 314164
              status: STATUS_SUCCESS
              metric_values { name { tag: "current_temp" } value: 1.0
                training_step: 1
                wall_time_secs: 1.0
              }
              metric_values { name { tag: "delta_temp" } value: 1.5
                training_step: 2
                wall_time_secs: 10.0
              }
            }
          }
          session_groups {
            name: "group_3"
            hparams { key: "bool_hparam" value { bool_value: true } }
            hparams { key: "final_temp" value { number_value: 120.0 } }
            hparams { key: "initial_temp" value { number_value: 300.0 } }
            hparams { key: "string_hparam" value { string_value: "a string_3"}}
            hparams {
              key: 'optional_string_hparam' value { string_value: 'BB' }
            }
            metric_values { name { tag: "current_temp" } value: 101.0
              training_step: 1
              wall_time_secs: 1.0
            }
            metric_values { name { tag: "delta_temp" } value: -151.0
              training_step: 2
              wall_time_secs: 10.0
            }
            sessions {
              name: "session_4"
              start_time_secs: 314159
              end_time_secs: 314164
              status: STATUS_SUCCESS
              metric_values { name { tag: "current_temp" } value: 101.0
                training_step: 1
                wall_time_secs: 1.0
              }
              metric_values { name { tag: "delta_temp" } value: -151.0
                training_step: 2
                wall_time_secs: 10.0
              }
            }
          }
          session_groups {
            name: "group_1"
            hparams { key: "bool_hparam" value { bool_value: true } }
            hparams { key: "final_temp" value { number_value: 150.0 } }
            hparams { key: "initial_temp" value { number_value: 270.0 } }
            hparams { key: "string_hparam" value { string_value: "a string" } }
            metric_values { name { tag: "current_temp" } value: 10
              training_step: 1
              wall_time_secs: 1.0
            }
            metric_values { name { tag: "delta_temp" } value: 15
              training_step: 2
              wall_time_secs: 10.0
            }
            metric_values { name { tag: "optional_metric" } value: 33
              training_step: 20
              wall_time_secs: 2.0
            }
            sessions {
              name: "session_1"
              start_time_secs: 314159
              end_time_secs: 314164
              status: STATUS_SUCCESS
              metric_values { name { tag: "current_temp" } value: 10
                training_step: 1
                wall_time_secs: 1.0
              }
              metric_values { name { tag: "delta_temp" } value: 15
                training_step: 2
                wall_time_secs: 10.0
              }
              metric_values { name { tag: "optional_metric" } value: 33
                training_step: 20
                wall_time_secs: 2.0
            }
            }
          }
          total_size: 3
        ''')
    #Primary key in descending order. Secondary key in ascending order.
    self._verify_handler(
        request='''
          col_params: {
            hparam: 'bool_hparam'
            order: ORDER_DESC
          }
          col_params: {
            metric: { tag: 'delta_temp' }
            order: ORDER_ASC
          }
        ''',
        expected_response='''
          session_groups {
            name: "group_3"
            hparams { key: "bool_hparam" value { bool_value: true } }
            hparams { key: "final_temp" value { number_value: 120.0 } }
            hparams { key: "initial_temp" value { number_value: 300.0 } }
            hparams { key: "string_hparam" value { string_value: "a string_3"}}
            hparams {
              key: 'optional_string_hparam' value { string_value: 'BB' }
            }
            metric_values { name { tag: "current_temp" } value: 101.0
              training_step: 1
              wall_time_secs: 1.0
            }
            metric_values { name { tag: "delta_temp" } value: -151.0
              training_step: 2
              wall_time_secs: 10.0
            }
            sessions {
              name: "session_4"
              start_time_secs: 314159
              end_time_secs: 314164
              status: STATUS_SUCCESS
              metric_values { name { tag: "current_temp" } value: 101.0
                training_step: 1
                wall_time_secs: 1.0
              }
              metric_values { name { tag: "delta_temp" } value: -151.0
                training_step: 2
                wall_time_secs: 10.0
              }
            }
          }
          session_groups {
            name: "group_1"
            hparams { key: "bool_hparam" value { bool_value: true } }
            hparams { key: "final_temp" value { number_value: 150.0 } }
            hparams { key: "initial_temp" value { number_value: 270.0 } }
            hparams { key: "string_hparam" value { string_value: "a string" } }
            metric_values { name { tag: "current_temp" } value: 10
              training_step: 1
              wall_time_secs: 1.0
            }
            metric_values { name { tag: "delta_temp" } value: 15
              training_step: 2
              wall_time_secs: 10.0
            }
            metric_values { name { tag: "optional_metric" } value: 33
              training_step: 20
              wall_time_secs: 2.0
            }
            sessions {
              name: "session_1"
              start_time_secs: 314159
              end_time_secs: 314164
              status: STATUS_SUCCESS
              metric_values { name { tag: "current_temp" } value: 10
                training_step: 1
                wall_time_secs: 1.0
              }
              metric_values { name { tag: "delta_temp" } value: 15
                training_step: 2
                wall_time_secs: 10.0
              }
              metric_values { name { tag: "optional_metric" } value: 33
                training_step: 20
                wall_time_secs: 2.0
            }
            }
          }
          session_groups {
            name: "group_2"
            hparams { key: "bool_hparam" value { bool_value: false } }
            hparams { key: "final_temp" value { number_value: 100.0 } }
            hparams { key: "initial_temp" value { number_value: 280.0 } }
            hparams { key: "string_hparam" value { string_value: "AAAAA"}}
            metric_values { name { tag: "current_temp" } value: 100
              training_step: 1
              wall_time_secs: 1.0
            }
            metric_values { name { tag: "delta_temp" } value: 150
              training_step: 2
              wall_time_secs: 10.0
            }
            sessions {
              name: "session_2"
              start_time_secs: 314159
              end_time_secs: 314164
              status: STATUS_SUCCESS
              metric_values { name { tag: "current_temp" } value: 100
                training_step: 1
                wall_time_secs: 1.0
              }
              metric_values { name { tag: "delta_temp" } value: 150
                training_step: 2
                wall_time_secs: 10.0
              }
            }
            sessions {
              name: "session_3"
              start_time_secs: 314159
              end_time_secs: 314164
              status: STATUS_SUCCESS
              metric_values { name { tag: "current_temp" } value: 1.0
                training_step: 1
                wall_time_secs: 1.0
              }
              metric_values { name { tag: "delta_temp" } value: 1.5
                training_step: 2
                wall_time_secs: 10.0
              }
            }
          }
          total_size: 3
        ''')

  def test_sort_one_column_with_missing_values(self):
    self._verify_handler(
        request='''
          col_params: {
            metric: { tag: 'optional_metric' }
            order: ORDER_ASC
          }
        ''',
        expected_response='''
          session_groups {
            name: "group_1"
            hparams { key: "bool_hparam" value { bool_value: true } }
            hparams { key: "final_temp" value { number_value: 150.0 } }
            hparams { key: "initial_temp" value { number_value: 270.0 } }
            hparams { key: "string_hparam" value { string_value: "a string" } }
            metric_values { name { tag: "current_temp" } value: 10
              training_step: 1
              wall_time_secs: 1.0
            }
            metric_values { name { tag: "delta_temp" } value: 15
              training_step: 2
              wall_time_secs: 10.0
            }
            metric_values { name { tag: "optional_metric" } value: 33
                training_step: 20
                wall_time_secs: 2.0
            }
            sessions {
              name: "session_1"
              start_time_secs: 314159
              end_time_secs: 314164
              status: STATUS_SUCCESS
              metric_values { name { tag: "current_temp" } value: 10
                training_step: 1
                wall_time_secs: 1.0
              }
              metric_values { name { tag: "delta_temp" } value: 15
                training_step: 2
                wall_time_secs: 10.0
              }
              metric_values { name { tag: "optional_metric" } value: 33
                training_step: 20
                wall_time_secs: 2.0
            }
            }
          }
          session_groups {
            name: "group_2"
            hparams { key: "bool_hparam" value { bool_value: false } }
            hparams { key: "final_temp" value { number_value: 100.0 } }
            hparams { key: "initial_temp" value { number_value: 280.0 } }
            hparams { key: "string_hparam" value { string_value: "AAAAA"}}
            metric_values { name { tag: "current_temp" } value: 100
              training_step: 1
              wall_time_secs: 1.0
            }
            metric_values { name { tag: "delta_temp" } value: 150
              training_step: 2
              wall_time_secs: 10.0
            }
            sessions {
              name: "session_2"
              start_time_secs: 314159
              end_time_secs: 314164
              status: STATUS_SUCCESS
              metric_values { name { tag: "current_temp" } value: 100
                training_step: 1
                wall_time_secs: 1.0
              }
              metric_values { name { tag: "delta_temp" } value: 150
                training_step: 2
                wall_time_secs: 10.0
              }
            }
            sessions {
              name: "session_3"
              start_time_secs: 314159
              end_time_secs: 314164
              status: STATUS_SUCCESS
              metric_values { name { tag: "current_temp" } value: 1.0
                training_step: 1
                wall_time_secs: 1.0
              }
              metric_values { name { tag: "delta_temp" } value: 1.5
                training_step: 2
                wall_time_secs: 10.0
              }
            }
          }
          session_groups {
            name: "group_3"
            hparams { key: "bool_hparam" value { bool_value: true } }
            hparams { key: "final_temp" value { number_value: 120.0 } }
            hparams { key: "initial_temp" value { number_value: 300.0 } }
            hparams { key: "string_hparam" value { string_value: "a string_3"}}
            hparams {
              key: 'optional_string_hparam' value { string_value: 'BB' }
            }
            metric_values { name { tag: "current_temp" } value: 101.0
              training_step: 1
              wall_time_secs: 1.0
            }
            metric_values { name { tag: "delta_temp" } value: -151.0
              training_step: 2
              wall_time_secs: 10.0
            }
            sessions {
              name: "session_4"
              start_time_secs: 314159
              end_time_secs: 314164
              status: STATUS_SUCCESS
              metric_values { name { tag: "current_temp" } value: 101.0
                training_step: 1
                wall_time_secs: 1.0
              }
              metric_values { name { tag: "delta_temp" } value: -151.0
                training_step: 2
                wall_time_secs: 10.0
              }
            }
          }
          total_size: 3
        ''')
    self._verify_handler(
        request='''
          col_params: {
            hparam: 'optional_string_hparam'
            order: ORDER_ASC
          }
        ''',
        expected_response='''
          session_groups {
            name: "group_3"
            hparams { key: "bool_hparam" value { bool_value: true } }
            hparams { key: "final_temp" value { number_value: 120.0 } }
            hparams { key: "initial_temp" value { number_value: 300.0 } }
            hparams { key: "string_hparam" value { string_value: "a string_3"}}
            hparams {
              key: 'optional_string_hparam' value { string_value: 'BB' }
            }
            metric_values { name { tag: "current_temp" } value: 101.0
              training_step: 1
              wall_time_secs: 1.0
            }
            metric_values { name { tag: "delta_temp" } value: -151.0
              training_step: 2
              wall_time_secs: 10.0
            }
            sessions {
              name: "session_4"
              start_time_secs: 314159
              end_time_secs: 314164
              status: STATUS_SUCCESS
              metric_values { name { tag: "current_temp" } value: 101.0
                training_step: 1
                wall_time_secs: 1.0
              }
              metric_values { name { tag: "delta_temp" } value: -151.0
                training_step: 2
                wall_time_secs: 10.0
              }
            }
          }
          session_groups {
            name: "group_1"
            hparams { key: "bool_hparam" value { bool_value: true } }
            hparams { key: "final_temp" value { number_value: 150.0 } }
            hparams { key: "initial_temp" value { number_value: 270.0 } }
            hparams { key: "string_hparam" value { string_value: "a string" } }
            metric_values { name { tag: "current_temp" } value: 10
              training_step: 1
              wall_time_secs: 1.0
            }
            metric_values { name { tag: "delta_temp" } value: 15
              training_step: 2
              wall_time_secs: 10.0
            }
            metric_values { name { tag: "optional_metric" } value: 33
              training_step: 20
              wall_time_secs: 2.0
            }
            sessions {
              name: "session_1"
              start_time_secs: 314159
              end_time_secs: 314164
              status: STATUS_SUCCESS
              metric_values { name { tag: "current_temp" } value: 10
                training_step: 1
                wall_time_secs: 1.0
              }
              metric_values { name { tag: "delta_temp" } value: 15
                training_step: 2
                wall_time_secs: 10.0
              }
              metric_values { name { tag: "optional_metric" } value: 33
                training_step: 20
                wall_time_secs: 2.0
              }
            }
          }
          session_groups {
            name: "group_2"
            hparams { key: "bool_hparam" value { bool_value: false } }
            hparams { key: "final_temp" value { number_value: 100.0 } }
            hparams { key: "initial_temp" value { number_value: 280.0 } }
            hparams { key: "string_hparam" value { string_value: "AAAAA"}}
            metric_values { name { tag: "current_temp" } value: 100
              training_step: 1
              wall_time_secs: 1.0
            }
            metric_values { name { tag: "delta_temp" } value: 150
              training_step: 2
              wall_time_secs: 10.0
            }
            sessions {
              name: "session_2"
              start_time_secs: 314159
              end_time_secs: 314164
              status: STATUS_SUCCESS
              metric_values { name { tag: "current_temp" } value: 100
                training_step: 1
                wall_time_secs: 1.0
              }
              metric_values { name { tag: "delta_temp" } value: 150
                training_step: 2
                wall_time_secs: 10.0
              }
            }
            sessions {
              name: "session_3"
              start_time_secs: 314159
              end_time_secs: 314164
              status: STATUS_SUCCESS
              metric_values { name { tag: "current_temp" } value: 1.0
                training_step: 1
                wall_time_secs: 1.0
              }
              metric_values { name { tag: "delta_temp" } value: 1.5
                training_step: 2
                wall_time_secs: 10.0
              }
            }
          }
          total_size: 3
        ''')

  def _verify_handler(self, request, expected_response):
    request_proto = api_pb2.ListSessionGroupsRequest()
    text_format.Merge(request, request_proto)
    handler = list_session_groups.Handler(
        backend_context.Context(self._mock_multiplexer),
        request_proto)
    response = handler.run()
    self.maxDiff = None
    # TODO(erez): Make this ignore different orders of repeated fields where
    # the order doesn't matter.
    self.assertProtoEquals(expected_response, response)

  def _serialized_plugin_data(self, data_oneof_field, text_protobuffer):
    oneof_type_dict = {
        DATA_TYPE_EXPERIMENT : api_pb2.Experiment,
        DATA_TYPE_SESSION_START_INFO : plugin_data_pb2.SessionStartInfo,
        DATA_TYPE_SESSION_END_INFO : plugin_data_pb2.SessionEndInfo
    }
    protobuffer = text_format.Merge(text_protobuffer,
                                    oneof_type_dict[data_oneof_field]())
    return metadata.create_summary_metadata(
        data_oneof_field, protobuffer).plugin_data.content


if __name__ == '__main__':
  tf.test.main()
