import marshmallow as ma
from marshmallow import pre_load, ValidationError
import numpy as np


class TranspilationRequest:
    def __init__(self, qpu_name, impl_language, impl_url, impl_data, bearer_token, input_params):
        self.qpu_name = qpu_name
        self.impl_language = impl_language
        self.impl_url = impl_url
        self.impl_data = impl_data
        self.bearer_token = bearer_token
        self.input_params = input_params


class ExecutionRequest:
    def __init__(self, qpu_name, impl_language, impl_url, transpiled_cirq_json, impl_data, bearer_token, shots, input_params):
        self.qpu_name = qpu_name
        self.impl_language = impl_language
        self.impl_url = impl_url
        self.impl_data = impl_data
        self.transpiled_cirq_json = transpiled_cirq_json
        self.bearer_token = bearer_token
        self.shots = shots
        self.input_params = input_params


class ResultRequest:
    def __init__(self, result_id):
        self.result_id = result_id

class TranspilationRequestSchema(ma.Schema):
    qpu_name = ma.fields.String(data_key="qpu-name")
    impl_language = ma.fields.String(data_key="impl-language")
    impl_url = ma.fields.String(data_key="impl-url")
    impl_data = ma.fields.String(data_key="impl-data")
    bearer_token = ma.fields.String(data_key="bearer-token")
    input_params = ma.fields.Mapping(data_key="input-params")


class ExecutionRequestSchema(ma.Schema):
    qpu_name = ma.fields.String(data_key="qpu-name")
    impl_language = ma.fields.String(data_key="impl-language")
    impl_url = ma.fields.String(data_key="impl-url")
    impl_data = ma.fields.String(data_key="impl-data")
    transpiled_cirq_json = ma.fields.String(data_key="transpiled-cirq-json")
    bearer_token = ma.fields.String(data_key="bearer-token")
    shots = ma.fields.Integer()
    input_params = ma.fields.Mapping(data_key="input-params")


class ResultRequestSchema(ma.Schema):
    result_id = ma.fields.String()
