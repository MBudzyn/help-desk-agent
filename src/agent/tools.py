"""LangChain wrappers around the shop tools. The functions themselves stay free of the model."""

from langchain_core.tools import tool

from tools import bookings, policies, refunds


@tool
def search_policies(query: str) -> str:
    """Find CityWheels policy sections about hours, prices, ages, or other shop rules.

    Pass the customer's question or a short topic. The result is the matching
    text from the shop documents, or a message that nothing matched.
    """
    return policies.search_policies(query)


@tool
def get_booking(booking_id: str) -> str:
    """Return one CityWheels booking, such as CW-1002.

    If that booking does not exist, the result says it was not found.
    """
    return bookings.get_booking(booking_id)


@tool
def calculate_refund(booking_id: str) -> str:
    """Calculate the refund for cancelling a booking at the shop's current time.

    Use this result for the amount. Do not calculate the money yourself.
    """
    return refunds.calculate_refund(booking_id)


SHOP_TOOLS = [search_policies, get_booking, calculate_refund]
