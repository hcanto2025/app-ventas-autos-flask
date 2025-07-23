from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Configura la ruta a tu chromedriver si no está en el PATH
driver = webdriver.Chrome()  # O pon: webdriver.Chrome(executable_path='ruta/a/chromedriver.exe')

# 1. Ingresar usuario y contraseña
driver.get("http://localhost:5000/clientes/login")  # Cambia el puerto si es necesario

email = driver.find_element(By.NAME, "correo")
password = driver.find_element(By.NAME, "contrasena")
email.send_keys("antonellagiuliuccidonoso@gmail.com")
password.send_keys("vito2311")
password.send_keys(Keys.RETURN)

# Espera a que cargue la página principal
WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.LINK_TEXT, "Autos")))

# 2. Ir al menú autos y agregar Peugeot 208 al carrito
driver.find_element(By.LINK_TEXT, "Autos").click()
WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "table")))

# Busca la fila del Peugeot 208 y haz clic en "Agregar al carrito"
filas = driver.find_elements(By.CSS_SELECTOR, ".tabla-autos tbody tr")
for fila in filas:
    if "Peugeot" in fila.text and "208" in fila.text:
        boton = fila.find_element(By.LINK_TEXT, "Agregar al carrito")
        boton.click()
        break

# 3. Ir al carrito, elegir medio de pago y finalizar compra
driver.find_element(By.CSS_SELECTOR, ".carrito a").click()
WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "form")))

# Selecciona "Transferencia" como medio de pago
select = driver.find_element(By.NAME, "medio_pago")
for option in select.find_elements(By.TAG_NAME, "option"):
    if option.text.strip().lower() == "transferencia":
        option.click()
        break

# Finaliza la compra
driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

# Espera un poco para ver el resultado
time.sleep(3)

# Puedes verificar que aparece el mensaje de éxito
assert "¡Compra realizada con éxito!" in driver.page_source

print("Prueba automatizada completada con éxito.")

driver.quit()
