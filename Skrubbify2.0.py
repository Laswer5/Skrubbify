
import pdfplumber as pdf
from math import ceil
import os

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
        text = ""
        items_delim = "----------------------------------------------------------------------------------------------------"

        for page in pages:
            text = text + page.extract_text()

        delim_idx = text.index(items_delim)
        text = text[delim_idx + len(items_delim):]
        delim_idx = text.index(items_delim)
        text = text[:delim_idx]

        text = text[100:]
        text = text.split('\n')

        return text          

def print_by_lines(str_arr):
    for i in str_arr:
        print(i)

def separate_name_amount_price(pdf_text):
    names, amount, prices = [], [], []

    for i in pdf_text:
        names.append(i[21:55])
        amount.append(i[55:58])
        prices.append(i[70:76])

    names = names[:len(names)-1]
    amount = amount[:len(amount)-1]
    prices = prices[:len(prices)-1]

    return names, amount, prices

def convert_to_num(str_arr):
    num_arr = []
    for i in str_arr:
        i = i.replace(',', '.')
        num_arr.append(float(i))
    
    return num_arr

def bootleg_ceil(number: float) -> int:
    if (ceil(number) - number) > 0.85:
        return round(number)
    else:
        return ceil(number)


def snabbgross_extract(pdf_path: str):
    pdf_data = read_pdf(pdf_path) 
    names, amounts, prices = separate_name_amount_price(pdf_data)
    amounts, prices = convert_to_num(amounts), convert_to_num(prices)

    calc_name, calc_price = [], []

    i = 0
    pant_bool = 0
    while i < len(names):
        curr_price = 0
        if "Bästa pris" in names[i]:
            continue
        else:
            if i+1 < len(names) and "PANT" in names[i+1]:
                curr_price = curr_price + prices[i+1]
                pant_bool = 1

            curr_price = curr_price + prices[i]
            sale_price = bootleg_ceil(curr_price / amounts[i])

            calc_name.append(names[i])
            calc_price.append(sale_price)

            if pant_bool == 0:
                i = i + 1
            elif pant_bool == 1:
                i = i + 2
                pant_bool = 0

    return calc_name, calc_price
        
def output_to_csv(item_names: str, item_prices: int):
    with open('Skrubbenpriser.txt', 'w', encoding='utf-8') as file:
        file.write(
            "Varunamn                          |   Pris inkl. moms & pant (SEK)")
        for x in range(len(item_names)):
            file.write('\n' + item_names[x] + "|" + "   " + str(item_prices[x]))



names, prices = snabbgross_extract('Kvitto.pdf')

output_to_csv(names, prices)