
"""
* Skrubbify                                     *
* Läser av och beräknar priser till skrubben    *
* från ett snabbgrosskvitto.                    *
* @Lukas LT, 2023                               *
"""

import pdfplumber as pdf
from math import ceil


def read_pdf(pdf_path: str) -> str:
    """
    Reads the receipt PDF-file.

        Parameters:
            pdf_path: File path to the pdf, as a string.

        Returns:
            Formatted receipt data.
    """
    with pdf.open(pdf_path) as receipt:
        pages = receipt.pages
        page = pages[0]
        text = ""
        items_delim = "----------------------------------------------------------------------------------------------------"

        text = page.extract_text_simple(x_tolerance=1, y_tolerance=1)

        delim_idx = text.index(items_delim)
        text = text[delim_idx + len(items_delim):]
        delim_idx = text.index(items_delim)
        text = text[:delim_idx]

        text = text[100:]
        text = text.split('\n')

        return text


def separate_name_amount_price(pdf_text) -> tuple[str, str, str]:
    """
    Splits each string line in the receipt and returns the 
    name, amount, and price, of each item in the receipt.

        Parameters:
            pdf_text: Parsed pdf-data

        Returns:
            Correctly formatted names, amounts, and prices.

        @NOTE: Uses hardcoded indexing from values specific to the
        PDF-reading parameters set in read_pdf(), might be subject
        to change if PDF structure changes.
    """

    names, amount, prices = [], [], []

    for i in pdf_text:
        names.append(i[21:55])
        amount.append(i[55:58])
        prices.append(i[70:76])

    names = names[:len(names)-1]  # Last index ends up empty, filter.
    amount = amount[:len(amount)-1]
    prices = prices[:len(prices)-1]

    return names, amount, prices


def convert_to_num(str_arr) -> float:
    """
    Converts string numbers to numerical value.
    Also replaces ',' with '.' as the ceil() function does not
    recognize ',' as the separator for this locale.

        Parameters:
            str_arr: Array of string numbers.

        Returns:
            str_arr converted to float.
    """

    num_arr = []
    for i in str_arr:
        i = i.replace(',', '.')

        if i != '':
            num_arr.append(float(i))
        else:
            num_arr.append(None)

    return num_arr


def bootleg_ceil(number: float) -> int:
    """
    Rounds to closest integer, with weighting by the 'skrubben-bankroll' variable,
    that deals with prices very close but larger than the nearest integer.

        Parameters:
            number: Float to round

        Returns:
            Int representation of float argument
    """

    skrubben_bankroll = 0.95

    if (ceil(number) - number) > skrubben_bankroll:
        return round(number)
    else:
        return ceil(number)


def filter_special_prices(pdf_data):
    """
    Filters out the empty 'Bästa pris' row from names, amounts, and prices.

        Parameters:
            pdf_data: Parsed pdf-data.
        
        Returns: filtered lists.
    """

    names, amounts, prices = separate_name_amount_price(pdf_data)

    filtered_names, filtered_amounts, filtered_prices = zip(
        *[(a, b, c) for a, b, c in zip(names, amounts, prices) if 'Bästa pris' not in a])

    return filtered_names, filtered_amounts, filtered_prices


def snabbgross_extract(pdf_path: str) -> tuple[str, int]:
    """
    Calculates prices for each snabbgross items using the functions
    above.

        Parameters:
            pdf_path: File path to receipt as a string

        Returns: 
            item_names: Array of item names.
            item_prices: Array of item prices.
    """

    pdf_data = read_pdf(pdf_path)
    names, amounts, prices = filter_special_prices(pdf_data)
    amounts, prices = convert_to_num(amounts), convert_to_num(prices)

    calc_name, calc_price = [], []

    i = 0
    while i < len(names):

        calc_name.append(names[i])

        price = bootleg_ceil(prices[i] / amounts[i])

        if i + 1 < len(names) and 'PANT' in names[i+1]:
            price = price + 1
            i = i + 2
        else:
            i = i + 1

        price = price + 2
        calc_price.append(price)

    return calc_name, calc_price


def output_to_csv(item_names: str, item_prices: int):
    """
    Writes item name and price to a .csv file

        Parameters:
            item_names: Array of item names as strings
            item_prices: Array of item prices as ints.
    """

    with open('Skrubbenpriser.txt', 'w', encoding='utf-8') as file:
        file.write(
            "Varunamn                          |   Pris inkl. moms & pant (SEK)")
        for x in range(len(item_names)):
            file.write('\n' + item_names[x] +
                       "|" + "   " + str(item_prices[x]))


def print_red(text: str):
    red_color = "\033[31m"  # ANSI escape code for red text
    reset_color = "\033[0m"  # ANSI escape code for resetting the color
    print(f"{red_color}{text}{reset_color}")


def main():

    print_red(
        "WARNING: CURRENTLY ONLY SUPPORTS PRICES LISTED ON FIRST PAGE OF RECEIPT!")
    print('Please input receipt file path:')
    print('(If in the same folder as this script, simply enter file name)')
    file_path = input()

    names, prices = snabbgross_extract(file_path)
    output_to_csv(names, prices)
    print('Printing prices..')


main()
