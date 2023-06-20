#!/usr/bin/env python3

import cv2
import pytesseract
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from skimage.metrics import structural_similarity as ssim
import numpy as np
from math import ceil

filename = "./images/whatsapp4"


def mse(imageA, imageB):
    # the 'Mean Squared Error' between the two images is the
    # sum of the squared difference between the two images;
    err = np.sum((imageA.astype("float") - imageB.astype("float")) ** 2)
    err /= float(imageA.shape[0] * imageA.shape[1])

    # return the MSE, the lower the error, the more "similar"
    # the two images are
    return err


def isUpper(charac):
    if (ord(charac) >= 65) and (ord(charac) <= 90):
        return True

    return False


if __name__ == '__main__':

    # Read image from which text needs to be extracted
    img = cv2.imread(filename + ".jpg")

    # Preprocessing the image starts

    # Convert the image to gray scale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.Canny(gray, 0, 255)

    # Performing OTSU threshold
    ret, thresh1 = cv2.threshold(gray, 0, 255,
                                 cv2.THRESH_OTSU | cv2.THRESH_BINARY)

    # Specify structure shape and kernel size.
    # Kernel size increases or decreases the area
    # of the rectangle to be detected.
    # A smaller value like (10, 10) will detect
    # each word instead of a sentence.
    rect_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (10, 10))

    # Applying dilation on the threshold image
    dilation = cv2.dilate(thresh1, rect_kernel, iterations=1)

    # Finding contours
    contours, hierarchy = cv2.findContours(dilation, cv2.RETR_EXTERNAL,
                                           cv2.CHAIN_APPROX_NONE)

    flag = 1
    if (flag == 1):
        cv2.imwrite(filename + "-gra.jpg", gray)
        cv2.imwrite(filename + "-dil.jpg", dilation)

    # Creating a copy of image
    im2 = img.copy()

    # Looping through the identified contours
    # Then rectangular part is cropped and passed on
    # to pytesseract for extracting text from it
    # Extracted text is then written into the text file

    text = ""

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)

        cut = ceil(w/8)

        only_carta = im2[y:y + h, x:x + w]
        cv2.imwrite(filename + "-crd.jpg", only_carta)

        # Drawing a rectangle on copied image
        rect = cv2.rectangle(im2, (x+cut, y), (x + w-cut*2, y + h), (0, 255, 0), 2)

        # Cropping the text block for giving input to OCR
        cropped = im2[y:y + h, x+cut:x + w-cut*2]

        # Apply OCR on the cropped image
        text = text + pytesseract.image_to_string(cropped)

    print(text)

    cv2.imwrite(filename + "-rec.jpg", im2)

    achou = 0
    for linha in text.split("\n"):
        name_l = linha
        print("linha: " + name_l)
        for palavra in name_l.split(" "):
            print("     palavra: " + palavra)
            if (len(palavra) > 0):
                print("     ord: " + str(ord(palavra[0])))
                if (isUpper(palavra[0])):
                    name = palavra
                    achou = 1
                    break

        if (achou == 1):
            break

    print("nome: " + name + "\n")

    url = "https://pokemoncard.io/card-database/?&n=" + name + \
           "&desc=" + name + "&supertype=Pokemon"

    print(url)

    driver = webdriver.Firefox()
    driver.set_page_load_timeout(10)
    driver.get(url)

    element_present = EC.presence_of_element_located((By.CLASS_NAME, "item-img"))
    WebDriverWait(driver, 4).until(element_present)

    html = driver.page_source
    html_lines = html.split("\n")
    html_api_part = ""
    substr = "<div id=\"api-area\">"

    for linha in html_lines:
        if (substr in str(linha)):
            html_api_part = linha
            break

    file = open("./recovered-html.html", "w+")
    file.write(html)
    file.close()

    cartas = ""
    file = open("./recovered-html_api_part.html", "w+")

    html_api_part = html_api_part.split("src=\"")

    for linha in html_api_part[1:]:
        link = linha.split(".png")[0]
        if link != linha:
            cartas = cartas + link + ".png\n"
            file.write(link + ".png\n")

    file.close()
    cartas = cartas.split("\n")[:-1]

    indice = 0
    max_i = 0
    max_match = 0

    for carta in cartas:
        tmpwd = "/home/smartgreen/Documentos/Projetinhos/PokeFinder/tmp/tmp.png"
        tmpwd2 = "/home/smartgreen/Documentos/Projetinhos/PokeFinder/tmp/tmp2.png"

        driver.get(carta)
        source_string = driver.page_source
        if "cannot be displayed" in source_string:
            indice = indice + 1
            continue

        driver.get_full_page_screenshot_as_file(tmpwd)

        img_carta = cv2.imread(tmpwd)
        img_carta = img_carta[150:493, 561:806]
        img_carta = cv2.resize(img_carta, (only_carta.shape[1], only_carta.shape[0]))

        img_carta = cv2.Canny(img_carta, 0, 255)
        only_carta = cv2.Canny(only_carta, 0, 255)

        # diffSSIM = ssim(only_carta, img_carta, channel_axis=2)
        diffSSIM = ssim(only_carta, img_carta)
        diffMSE = mse(only_carta, img_carta)

        diff = diffSSIM * diffMSE

        print("carta: " + carta + "\ndiff: " + str(diff) + "\n\n")
        if (diff > max_match):
            max_i = indice
            max_match = diff

        indice = indice + 1

    print(cartas[max_i])

    # try:
    #     request_site = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    #     page = urlopen(request_site)
    #     html_bytes = page.read()
    #     html = html_bytes.decode("utf-8")
    # 
    #     file = open("./recovered-html.html", "w+")
    #     file.write(html)
    #     file.close()
    # 
    # except HTTPError as erro:
    #     print("Erro: " + str(erro))