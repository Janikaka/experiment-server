from experiment_server.models import (Configuration, ConfigurationKey, ExclusionConstraint, Operator, RangeConstraint)
import _operator

# TODO: Return descriptive error messages on failure, so it can be passed from backend to frontend

def get_valid_types():
    return ["boolean", "string", "integer", "float"]

def get_operators():
    if Operator.query().count == 0:
        op1 = Operator(id=1, math_value='=', human_value='equals')
        op2 = Operator(id=2, math_value='<=', human_value='less or equal than')
        op3 = Operator(id=3, math_value='<', human_value='less than')
        op4 = Operator(id=4, math_value='>=', human_value='greater or equal than')
        op5 = Operator(id=5, math_value='>', human_value='greater than')
        op6 = Operator(id=6, math_value='!=', human_value='not equal')
        op7 = Operator(id=7, math_value='[]', human_value='inclusive')
        op8 = Operator(id=8, math_value='()', human_value='exclusive')
        op9 = Operator(id=9, math_value='def', human_value='must define')
        op10 = Operator(id=10, math_value='ndef', human_value='must not define')

        Operator.save(op1)
        Operator.save(op2)
        Operator.save(op3)
        Operator.save(op4)
        Operator.save(op5)
        Operator.save(op6)
        Operator.save(op7)
        Operator.save(op8)
        Operator.save(op9)
        Operator.save(op10)

    return Operator.all()

def is_valid_type_operator(type, operator):
    """
    Validates type that it can be used with given operator
    :param type: Type to be validated
    :param operator: Operator to be used with given type
    :return: is type valid with given operator
    """
    if operator is None:
        return True
    if type == "boolean" or type == "string":
        return operator.id == 1 or operator.id == 6 or operator.id == 9 or operator.id == 10

    return type == "integer" or type == "float"

def is_valid_type_value(type, value):
    """
    Validates value's type to be equal with given type
    :param type: Desired type
    :param value: Value to be validated. Can be None since ExclusionConstraint can hold None values
    :return: Is value Valid to given Type
    """
    if value is None:
        return True

    try:
        if type == "boolean":
            bool(value)
            if (isinstance(value, str) or value > 1 or value < 0):
                raise ValueError("If integer is something else besides 0 or 1,",
                                 " it will not be considered as boolean in this case.")
        elif type == "string":
            str(value)
        elif type == "integer":
            int(value)
        elif type == "float":
            float(value)
    except ValueError as e:
        return False

    return True


def is_valid_type_values(type, operator, values):
    """
    Validates multiple values' type and operators.
    :param type: Desired Type
    :param operator: Desired Operator
    :param values: Value to be validated
    :return: Are given values Valid
    """
    if operator is not None and (operator.id == 7 or operator.id == 8) and (len(values) < 2 or values[1] is None):
        return False

    for value in values:
        if not is_valid_type_value(type, value):
            return False

    return True


def get_value_as_correct_type(value, type):
    if value is None:
        return None
    if type == "string":
        return str(value)
    elif type == "integer":
        return int(value)
    elif type == "float":
        return float(value)
    elif type == "boolean":
        return bool(value)

def evaluate_value_operator(operator, given_value, value1, value2):
    """
    Validates given_value by comparing it with operator to value1 and value 2. If operator with id less than 6 is given,
     only value1 is needed. Expects values to be in correct type.
    :param operator:
    :param given_value:
    :param value1:
    :param value2:
    :return:
    """
    ops = {'=': _operator.eq,
           '<=': _operator.le,
           '<': _operator.lt,
           '>=': _operator.ge,
           '>': _operator.gt,
           '!=': _operator.ne,
           }

    if operator.math_value == '[]' or operator.math_value == '()':
        if value1 is None or value2 is None:
            return False
        if operator.math_value == '[]':
            return value1 <= given_value <= value2
        elif operator.math_value == '()':
            return value1 < given_value < value2
    elif operator.math_value == 'def':
        return given_value is not None
    elif operator.math_value == 'ndef':
        return given_value is None
    elif operator.math_value is not None:
        return ops[operator.math_value](given_value, value1)

    return False


def is_in_range(configkey, value):
    """
    Checks RangeConstraints on given value. Assumes that Application- and ConfigurationKey-connection is already
    checked.
    :param configkey: Given ConfigurationKey
    :param value: Value to validate
    :return: Is given value approved by RangeConstraints
    """
    rangeconstraints = RangeConstraint.query().join(ConfigurationKey).filter(ConfigurationKey.id == configkey.id)

    for rc in rangeconstraints:
        if not evaluate_value_operator(Operator.get(rc.operator_id), get_value_as_correct_type(value, configkey.type),
                                       get_value_as_correct_type(rc.value, configkey.type), None):
            return False

    return True


def is_valid_exclusion(configkey, configuration):
    """
    Checks ExclusionConstraints on given value. It checks if value would break any argument "if a then b", when given
    value is in argument b. Only case this function needs to check, is that "a is false and b is true" does not happen.
    Assumes that Application- and ConfigurationKey-connection is already checked.
    :param configkey:
    :param configuration:
    :return:
    """
    exclusionconstraints = ExclusionConstraint.query().join(ConfigurationKey,
                                                            ExclusionConstraint.second_configurationkey)\
        .filter(ConfigurationKey.id == configkey.id)

    for exc in exclusionconstraints:
        ck_a = ConfigurationKey.get(exc.first_configurationkey_id).one_or_none()

        config_a = Configuration().query().filter(Configuration.experimentgroup_id == configuration.experimentgroup_id,
                                                 Configuration.key == ck_a.name).one_or_none()

        if config_a is None:
            return True

        op_a = Operator.get(exc.first_operator_id)
        type_a = ck_a.type
        value_a = get_value_as_correct_type(config_a.value, type_a)
        argument_a = evaluate_value_operator(op_a, value_a, exc.first_value_a, exc.first_value_b)

        op_b = Operator.get(exc.second_operator_id)
        type_b = configkey.type
        value_b = get_value_as_correct_type(configuration.value, type_b)
        argument_b = evaluate_value_operator(op_b, value_b, exc.second_value_a, exc.second_value_b)

        if not argument_a and argument_b:
            return False

    return True

