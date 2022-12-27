"""
Skrubbify
Extract unit prices from a standard snabbgross receipt to a csv file
Author: Lukas Lindén Thöming, 2022
NOTE: Static design, not guaranteed to work if standard format of receipt is changed.

"""

import os
import pdfplumber
from math import ceil
import tkinter as tk
from tkinter import filedialog

currentItemDelimiterStart = "Artikelnummer"
currentItemDelimiterStop = "-"


def pdfExtract(filepath: str):
    with pdfplumber.open(filepath) as pdf:

        page = pdf.pages[0]  # Get the first page of the PDF
        text = page.extract_text()  # Extract the text from the page

        # Very rare for two pages to be needed, not generalized for more than this.
        if len(pdf.pages) > 1:
            pageTwo = pdf.pages[1]
            text = text + "\n" + pageTwo.extract_text()

    splitByLine = text.split("\n")
    return splitByLine


def isolateItems(itemList):
    newList = []
    delimCount = 0

    for x in itemList:
        if x.startswith(currentItemDelimiterStart) == False and delimCount == 0:
            continue
        elif x.startswith(currentItemDelimiterStart) == True:
            delimCount = 1
        elif delimCount == 1 and x.startswith(currentItemDelimiterStop) == False:
            newList.append(x)
        elif x.startswith(currentItemDelimiterStop) == True:
            break

    return newList


def splitLinesByStrIndex(isolatedItems, start, stop):
    itemNames = []

    for item in isolatedItems:
        # Receipt uses constant whitespace for item names, might have to be modified if this changes.
        itemName = item[start:stop]
        itemNames.append(itemName)

    return itemNames

# item[21:55] -- String index for item names
# á-pris -- String index for item names: 70-76
# Förp -- String index for amount per package - 55-58


def isolateItemNames(isolatedItems): return splitLinesByStrIndex(
    isolatedItems, 21, 55)


def isolateUnitAmountPerPackage(isolatedItems): return splitLinesByStrIndex(
    isolatedItems, 55, 58)  # Only accounts for maximum of hundreds of units


def isolateUnitPrices(isolatedItems):
    pricesList = splitLinesByStrIndex(isolatedItems, 70, 76)
    formattedPricesList = []
    for x in pricesList:
        formattedPricesList.append(x.replace(',', '.'))
    return formattedPricesList


def printLines(lines):  # Helper debug function
    for x in range(len(lines)):
        print(lines[x])


def filterBestPrice(isolatedItems, isolatedPrice, isolatedUnitAmountPerPackage):
    filteredItemList = []
    filteredPriceList = []
    filteredIsolatedUnitAmountPerPackageList = []
    listLen = len(isolatedItems)

    for x in range(listLen):
        if "Bästa pris" not in isolatedItems[x]:
            if "Eur Pall" not in isolatedItems[x]:
                filteredItemList.append((isolatedItems[x]))
                filteredPriceList.append(isolatedPrice[x])
                filteredIsolatedUnitAmountPerPackageList.append(
                    isolatedUnitAmountPerPackage[x])

    return filteredItemList, filteredPriceList, filteredIsolatedUnitAmountPerPackageList


def snabbgrossExtract(pdfPath: str):
    isolatedItems = isolateItemNames(isolateItems(pdfExtract(pdfPath)))
    isolatedUnitPrices = isolateUnitPrices(isolateItems(pdfExtract(pdfPath)))
    isolatedUnitAmountsPerPackage = isolateUnitAmountPerPackage(
        isolateItems(pdfExtract(pdfPath)))

    filteredItemList, filteredPriceList, filteredUnitAmountList = filterBestPrice(
        isolatedItems, isolatedUnitPrices, isolatedUnitAmountsPerPackage)

    return filteredItemList, filteredPriceList, filteredUnitAmountList


items, prices, unitAmounts = snabbgrossExtract('receipt.pdf')


def bootleg_ceil(number):
    if (ceil(number) - number) > 0.85:
        return round(number)
    else:
        return ceil(number)


def calculatePricesReturnAsLists(itemNames: list, itemPrices: list, isolatedUnitAmountPerPackage: list):
    listLength = len(itemNames)
    VAT = 1.12  # 12% VAT for foodstuffs
    assert (listLength != 0)
    assert (listLength == len(itemPrices))
    assert (listLength == len(isolatedUnitAmountPerPackage))

    ItemAndPriceTupleList = []

    i = 0
    while i < listLength:
        if i+1 < listLength and "PANT" in itemNames[i + 1]:
            pantToBeAdded = float(itemPrices[i + 1])
            itemName = itemNames[i]
            itemPrice = float(itemPrices[i])
            itemAmountPerPackage = int(isolatedUnitAmountPerPackage[i])

            pricePerUnit = bootleg_ceil(
                ((itemPrice + pantToBeAdded) * VAT) / itemAmountPerPackage)

            ItemAndPriceTupleList.append([itemName, pricePerUnit])
            i = i+1
        else:
            itemName = itemNames[i]
            itemPrice = float(itemPrices[i])
            itemAmountPerPackage = int(isolatedUnitAmountPerPackage[i])
            pricePerUnit = bootleg_ceil(
                (itemPrice * 1.12) / itemAmountPerPackage)

            ItemAndPriceTupleList.append([itemName, pricePerUnit])

        i = i+1

    return ItemAndPriceTupleList


def snabbgrossCalculate(pdfPath: str):
    items, prices, unitAmounts = snabbgrossExtract(pdfPath)
    calculatedList = calculatePricesReturnAsLists(items, prices, unitAmounts)

    return calculatedList


def snabbgrossExport(pdfPath: str):

    priceList = snabbgrossCalculate(pdfPath)

    with open('Skrubbenpriser.txt', 'w', encoding='utf-8') as file:
        file.write("Varunamn                          |   Pris inkl. moms & pant (SEK)")
        for x in priceList:
            file.write('\n' + x[0] + "|" + "   " + str(x[1]))


def main():

    root = tk.Tk()
    root.withdraw()
    tk.messagebox.showinfo(title='Attention', message='Please select the receipt PDF in the pop-up window')

    pdf_path = filedialog.askopenfilename()
    snabbgrossExport(pdf_path)
    #outputPath = 'Skrubbenpriser.txt' Not yet implemented

    #os.system(r"Skrubbenpriser.txt")

main()
