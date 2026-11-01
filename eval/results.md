# Evaluation results

10 of 12 passed.

## saturday-hours — failed

- missing text: 08:00–20:00

Tools: search_policies

We open at 08:00 on Saturdays (from April to October).

## ebike-day-price — passed

Tools: search_policies

An electric bike (e-bike) is 40 EUR for a whole day (up to 24 hours).

## fourteen-year-old — passed

Tools: search_policies

No, an e-bike requires the rider to be at least 16 years old. 

However, a 14-year-old can rent a city bike (available from 13 years old, with a parent or guardian required to sign the rental).

## shop-location — passed

Tools: search_policies

The shop is located at the main entrance of the Riverside Park, next to the tram stop "Park Nadrzeczny".

## unknown-booking — passed

Tools: get_booking

Booking CW-9999 was not found. If you need further assistance, please contact the staff at help@citywheels.example or +48 000 000 000.

## refund-cw-1002 — passed

Tools: calculate_refund

You will receive a total refund of **340.00 EUR**, which breaks down as follows:
- **Rental refund:** 40.00 EUR (50% of the 80.00 EUR rental fee, since you are cancelling 33 hours before the start)
- **Booking fee refund:** 0.00 EUR (the 2.00 EUR booking fee is non-refundable)
- **Deposit refund:** 300.00 EUR

The refund will be sent back to your card within 5 working days.

## refund-cw-1004 — passed

Tools: calculate_refund

For booking CW-1004, you will receive a total refund of 73.00 EUR. 

This breakdown includes:
- **Rental refund:** 23.00 EUR (100% of the 23.00 EUR)
- **Booking fee refund:** 0.00 EUR (the 2.00 EUR fee is not refunded)
- **Deposit refund:** 50.00 EUR

Because the booking was paid with a voucher, the refund will be issued as a new voucher for 73.00 EUR rather than cash.

## refund-cw-1005 — passed

Tools: calculate_refund

Booking CW-1005 cannot be cancelled because its status is already cancelled. Nothing is refunded (0.00 EUR).

## bad-weather — failed

- missing staff contact

Tools: search_policies

If the weather service issues a storm warning for the day of the rental, you may get a full refund, but bad-weather refunds are decided by the staff. You will need to contact the staff to request this.

## change-dates — passed

Tools: search_policies

Yes, the dates or the bike type of a `confirmed` booking can be changed for free up to 24 hours before the start, provided that bikes are available. 

Later changes are not possible; if it is less than 24 hours before the start, you would have to cancel and book again.

## capital-of-australia — passed

Tools: none

I cannot answer that question as it is not about CityWheels. Please contact the staff at help@citywheels.example or +48 000 000 000.

## flight-to-paris — passed

Tools: none

That is not about CityWheels. Please contact the staff at help@citywheels.example or +48 000 000 000.
