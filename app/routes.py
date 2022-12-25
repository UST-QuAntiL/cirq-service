# ******************************************************************************
#  Copyright (c) 2021 University of Stuttgart
#
#  See the NOTICE file(s) distributed with this work for additional
#  information regarding copyright ownership.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
# ******************************************************************************
import cirq
from flask_smorest import Blueprint

from app import app, cirq_handler, implementation_handler, db, parameters
from app.result_model import Result
from flask import jsonify, abort, request
import logging
import json
import base64
from cirq import Circuit
import traceback
from app.request_schemas import TranspilationRequestSchema, TranspilationRequest, ExecutionRequestSchema, \
    ExecutionRequest, ResultRequestSchema, ResultRequest
from app.response_schemas import TranspilationResponseSchema, TranspilationResponse, ExecutionResponseSchema, \
    ExecutionResponse, ResultResponseSchema, ResultResponse

blp = Blueprint(
    "routes",
    __name__,
    url_prefix="/cirq-service/api/v1.0/",
    description="All Cirq-Service endpoints",
)


@blp.route("/transpile", methods=["POST"])
@blp.arguments(
    TranspilationRequestSchema,
    example={
        "impl_url": "https://raw.githubusercontent.com/UST-QuAntiL/cirq-service/main/Sample%20Implementations/ciruit_json.json",
        "impl_language": "Cirq-JSON",
        "qpu_name": "Sycamore"
    }
)
@blp.response(200, TranspilationResponseSchema)
def transpile_circuit(json: TranspilationRequest):
    """Get implementation from URL. Pass input into implementation. Generate and transpile circuit
    and return depth and width."""

    if not json:
        abort(400)

    qpu_name = json.get('qpu_name')
    impl_language = json.get('impl_language', '')
    input_params = json.get('input_params', "")
    impl_url = json.get('impl_url', "")
    bearer_token = json.get("bearer_token", "")
    app.logger.info("The input params are:" + str(input_params))
    if input_params != "":
        input_params = parameters.ParameterDictionary(input_params)
    # adapt if real backends are available
    token = ''
    # if 'token' in input_params:
    #     token = input_params['token']
    # elif 'token' in request.json:
    #     token = request.json.get('token')
    # else:
    #     abort(400)

    if impl_url is not None and impl_url != "":
        impl_url = json.get('impl_url')
        if impl_language.lower() == 'cirq-json':
            short_impl_name = 'no name'
            circuit = implementation_handler.prepare_code_from_cirq_url(impl_url, bearer_token)
        else:
            short_impl_name = "untitled"
            try:
                circuit = implementation_handler.prepare_code_from_url(impl_url, input_params, bearer_token)
            except ValueError:
                abort(400)

    elif 'impl-data' in json:
        impl_data = base64.b64decode(json.get('impl_data').encode()).decode()

        short_impl_name = 'no short name'
        if impl_language.lower() == 'cirq-json':
            circuit = implementation_handler.prepare_code_from_cirq_json(impl_data)
        else:
            try:
                circuit = implementation_handler.prepare_code_from_data(impl_data, input_params)
            except ValueError:
                abort(400)
    else:
        abort(400)

    try:
        transpiled_circuit: Circuit = cirq_handler.transpile_for_qpu(qpu_name, circuit)

        # count number of gates, multi qubit gates and measurements operation, by iterating over all operations
        number_of_multi_qubit_gates = 0
        number_of_measurement_operations = 0
        total_number_of_gates = 0
        for operation in transpiled_circuit.all_operations():
            if type(operation) is cirq.GateOperation:
                total_number_of_gates += 1
                if cirq.is_measurement(operation):
                    number_of_measurement_operations += 1
                elif len(operation.qubits) > 1:
                    number_of_multi_qubit_gates += 1

        # width: the amount of qubits
        width = len(transpiled_circuit.all_qubits())

        # gate_depth: the longest subsequence of compiled instructions where adjacent instructions share resources
        # Cirq packs gates as tight as possible in new circuits, the number of moments then is equal to the depth
        depth = len(cirq.Circuit(transpiled_circuit.all_operations()))

        # multi_qubit_gate_depth: Maximum number of successive two-qubit gates in the native cirq program;
        multi_qubit_gate_depth = len(cirq.Circuit([i for i in transpiled_circuit.all_operations()
                                                   if len(i.qubits) > 1]))

        # count number of single qubit gates
        number_of_single_qubit_gates = total_number_of_gates - number_of_multi_qubit_gates

        # count total number of all operations including gates and measurement operations
        total_number_of_operations = total_number_of_gates + number_of_measurement_operations
    except NotImplementedError:
        app.logger.info(f"QPU {qpu_name} is not supported!")
        abort(400)
    except Exception:
        app.logger.info(f"Transpile {short_impl_name} for {qpu_name}.")
        app.logger.info(traceback.format_exc())
        return jsonify({'error': 'transpilation failed'}), 200

    app.logger.info(f"Transpile {short_impl_name} for {qpu_name}: "
                    f"w={width}, "
                    f"d={depth}, "
                    f"total number of operations={total_number_of_operations}, "
                    f"number of single qubit gates={number_of_single_qubit_gates}, "
                    f"number of multi qubit gates={number_of_multi_qubit_gates}, "
                    f"number of measurement operations={number_of_measurement_operations}, "
                    f"multi qubit gate depth={multi_qubit_gate_depth}")

    return TranspilationResponse(depth, multi_qubit_gate_depth, width, total_number_of_operations,
                                 number_of_single_qubit_gates, number_of_multi_qubit_gates,
                                 number_of_measurement_operations, cirq.to_json(transpiled_circuit, indent=4))


@blp.route("/execute", methods=["POST"])
@blp.arguments(
    ExecutionRequestSchema,
    example={
        "impl_url": "https://raw.githubusercontent.com/UST-QuAntiL/cirq-service/main/Sample%20Implementations/ciruit_json.json",
        "impl_language": "Cirq-JSON",
        "qpu_name": "Sycamore"
    }
)
@blp.response(202, ExecutionResponseSchema)
def execute_circuit(json: ExecutionRequest):
    """Put execution job in queue. Return location of the later result."""
    if not json:
        abort(400)
    qpu_name = json.get('qpu_name')
    impl_language = json.get('impl_language', '')
    impl_url = json.get('impl_url')
    bearer_token = json.get("bearer_token", "")
    impl_data = json.get('impl_data')
    transpiled_cirq_json = json.get('transpiled_cirq_json', "")
    input_params = json.get('input_params', "")
    if input_params != "":
        input_params = parameters.ParameterDictionary(input_params)
    shots = request.json.get('shots', 1024)
    if 'token' in input_params:
        token = input_params['token']
    elif 'token' in request.json:
        token = request.json.get('token')
    else:
        token = ""

    job = app.execute_queue.enqueue('app.tasks.execute', impl_url=impl_url, impl_data=impl_data,
                                    impl_language=impl_language, transpiled_cirq_json=transpiled_cirq_json,
                                    qpu_name=qpu_name,
                                    token=token, input_params=input_params, shots=shots, bearer_token=bearer_token)
    result = Result(id=job.get_id(), backend=qpu_name, shots=shots)
    db.session.add(result)
    db.session.commit()

    logging.info('Returning HTTP response to client...')
    content_location = '/cirq-service/api/v1.0/results/' + result.id
    response = ExecutionResponse(content_location)
    response.status_code = 202
    response.headers.set("Location", content_location)
    return response


@app.route('/cirq-service/api/v1.0/calculate-calibration-matrix', methods=['POST'])
def calculate_calibration_matrix():
    """Put calibration matrix calculation job in queue. Return location of the later result."""
    pass


@blp.route("/results/<string:result_id>", methods=["GET"])
@blp.response(200, ResultResponseSchema)
def get_result(result_id):
    """Return result when it is available."""
    result = Result.query.get(str(result_id).strip())
    if result.complete:
        result_histogram = json.loads(result.result)
        response = ResultResponse(result.id, result.complete, result_histogram, result.backend, result.shots)
    else:
        response = ResultResponse(result.id, result.complete)
    return response


@blp.route("/version", methods=["GET"])
@blp.response(200)
def version():
    """Return current version number."""
    return jsonify({'version': '1.0'})
