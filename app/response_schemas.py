import marshmallow as ma
from flask import Response


class TranspilationResponse:
    def __init__(self, depth, multi_qubit_gate_depth, width, total_number_of_operations, number_of_single_qubit_gates, number_of_multi_qubit_gates, number_of_measurement_operations, transpiled_cirq_json):
        self.depth = depth
        self.multi_qubit_gate_depth = multi_qubit_gate_depth
        self.width = width
        self.total_number_of_operations = total_number_of_operations
        self.number_of_single_qubit_gates = number_of_single_qubit_gates
        self.number_of_multi_qubit_gates = number_of_multi_qubit_gates
        self.number_of_measurement_operations = number_of_measurement_operations
        self.transpiled_cirq_json = transpiled_cirq_json

    def to_json(self):
        json_response = {'depth': self.depth,
                    'multi-qubit-gate-depth': self.multi_qubit_gate_depth,
                    'width': self.width,
                    'total-number-of-operations': self.total_number_of_operations,
                    'number-of-single-qubit-gates': self.number_of_single_qubit_gates,
                    'number-of-multi-qubit-gates': self.number_of_multi_qubit_gates,
                    'number-of-measurement-operations': self.number_of_measurement_operations,
                    'transpiled-cirq-json': self.transpiled_cirq_json}
        return json_response


class ExecutionResponse(Response):
    def __init__(self, location):
        super().__init__()
        self.location = location

    def to_json(self):
        json_response = {'Location': self.location}
        return json_response


class ResultResponse:
    def __init__(self, id, complete, result = None, backend = None, shots = None):
        self.id = id
        self.complete = complete
        self.result = result
        self.backend = backend
        self.shots = shots

    def to_json(self):
        if self.result and self.backend and self.shots:
            return {'id': self.id, 'complete': self.complete, 'result': self.result,
                            'backend': self.backend, 'shots': self.shots}
        else:
            return {'id': self.id, 'complete': self.complete}


class TranspilationResponseSchema(ma.Schema):
    depth = ma.fields.Integer()
    multi_qubit_gate_depth = ma.fields.Integer(data_key="multi-qubit-gate-depth")
    width = ma.fields.Integer()
    total_number_of_operations = ma.fields.Integer(data_key="total-number-of-operations")
    number_of_single_qubit_gates = ma.fields.Integer(data_key="number-of-single-qubit-gates")
    number_of_multi_qubit_gates = ma.fields.Integer(data_key="number-of-multi-qubit-gates")
    number_of_measurement_operations = ma.fields.Integer(data_key="number-of-measurement-operations")
    transpiled_cirq_json = ma.fields.String(data_key="transpiled-cirq-json")


class ExecutionResponseSchema(ma.Schema):
    location = ma.fields.String()


class ResultResponseSchema(ma.Schema):
    id = ma.fields.UUID()
    complete = ma.fields.Boolean()
    result = ma.fields.Mapping()
    backend = ma.fields.String()
    shots = ma.fields.Integer()