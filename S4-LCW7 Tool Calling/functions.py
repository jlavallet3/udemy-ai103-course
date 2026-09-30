"""
This module contains functions for calculating loan repayments and total loan amounts based on various parameters.
"""


# This calculate_repayments_from_loan calculates the monthly repayments and total repayment amount for a given loan based on the principal, interest rate, and term in years.
def calculate_repayments_from_loan(
    principal: float, interest_rate: float, term_years: int
) -> Dict[str, Any]:
    """Calculate monthly repayments for a loan."""
    monthly_interest_rate = interest_rate / 12
    number_of_payments = term_years * 12

    if monthly_interest_rate == 0:
        monthly_repayment = principal / number_of_payments
    else:
        monthly_repayment = (
            principal
            * monthly_interest_rate
            / (1 - (1 + monthly_interest_rate) ** -number_of_payments)
        )

    total_repayment = monthly_repayment * number_of_payments

    return {
        "monthly_repayment": round(monthly_repayment, 2),
        "total_repayment": round(total_repayment, 2),
    }


# This calculate_total_loan_from_desired_repayment calculates the total loan amount based on desired monthly repayments, interest rate, and term in years.
def calculate_total_loan_from_desired_repayment(
    desired_monthly_repayment: float, interest_rate: float, term_years: int
) -> Dict[str, Any]:
    """Calculate the total loan amount based on desired monthly repayments."""
    monthly_interest_rate = interest_rate / 12
    number_of_payments = term_years * 12

    if monthly_interest_rate == 0:
        total_loan_amount = desired_monthly_repayment * number_of_payments
    else:
        total_loan_amount = (
            desired_monthly_repayment
            * (1 - (1 + monthly_interest_rate) ** -number_of_payments)
            / monthly_interest_rate
        )

    return {
        "total_loan_amount": round(total_loan_amount, 2),
    }
