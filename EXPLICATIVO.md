El score va de 0 a 10 y después se convierte en prioridad:

A: muy buen fit
B: posible buen fit
C: bajo fit o falta información
Qué mira el sistema

El sistema revisa datos del lead y señales encontradas en su web:

si tiene local físico
si tiene ecommerce
si vende por WhatsApp
si aparece MercadoLibre
si parece tener varias sucursales
si habla de stock, catálogo, envíos o compra online
si tiene una web profesional
si tiene algún canal de contacto claro
si pertenece a una industria interesante para ENVI

------------------------------------------------------------

Cómo suma puntos

Hoy la lógica base es esta:

+2 si parece ser un negocio físico
Porque ENVI está pensado para comercios con operación real, stock y ventas.

+2 si tiene ecommerce o compra online
Porque combinar local físico + online suele generar problemas de stock y gestión.

+2 si parece tener varias sucursales
Porque una operación multisucursal necesita más control.

+2 si hay señales de stock complejo
Por ejemplo frases como “consultar stock”, “catálogo”, “sin stock”, “stock disponible”.

+1 si vende o atiende por WhatsApp
Porque muchos pedidos terminan quedando desordenados si no hay sistema.

+1 si tiene una web profesional
Porque suele indicar un negocio más armado y con más capacidad de compra.

+0.5 si tiene canal de contacto claro
Email, WhatsApp o Instagram.

+1 si pertenece a una industria ideal
Por ejemplo ferretería, repuestera, pet shop, bazar, perfumería, ropa, electricidad o dietética.

El total se limita a 10 puntos máximo.

Prioridades

Después el sistema traduce el score:

7 a 10  = Prioridad A
4 a 6.9 = Prioridad B
0 a 3.9 = Prioridad C

-------------------------------------------------------------------------------

Cómo sabe cada cosa la app

Tiene web
Sale de Google Maps vía SerpAPI.

En el código, SerpAPI devuelve website y lo guardamos en el lead.

Confiabilidad: bastante buena si Google Maps lo trae.

Tiene teléfono
También viene de Google Maps/SerpAPI como phone.

Además, si el lead tiene web, el scraper revisa el texto de la web y busca patrones de teléfono.

Confiabilidad: media/buena. Puede agarrar teléfonos de la web, pero no siempre sabe si es ventas, soporte o administración.

Tiene WhatsApp
La app lo detecta revisando links dentro de la web.

Busca links como:

wa.me
api.whatsapp.com
También si aparece texto como whatsapp o pedidos por whatsapp, marca señal de venta por WhatsApp.

Confiabilidad:

Alta si encontró link real wa.me o api.whatsapp.com.
Media si solo encontró la palabra “WhatsApp”.
Tiene Instagram
La app entra a la web del comercio y busca links que apunten a instagram.com.

Confiabilidad: buena si la web tiene el link.

Limitación: si el negocio tiene Instagram pero no lo puso en su web, no lo detecta.

Tiene email
La app lee el texto de la web y busca algo con formato de email, tipo:

contacto@negocio.com
Confiabilidad: media/buena.

Puede pasar que encuentre un email genérico, viejo o no comercial.

Ecommerce detectado
La app revisa el HTML/texto de la web y busca señales como:

comprar
carrito
checkout
tienda online
compra online
envíos a todo el país
Confiabilidad: media.

No confirma que el ecommerce funcione. Solo dice: “hay señales de venta online”.

Stock complejo
La app busca frases como:

consultar stock
sin stock
stock disponible
catálogo
sku
mayorista
Confiabilidad: media.

Es una inferencia razonable: si habla de stock/catálogo, probablemente maneja productos y operación.

Posible multisucursal
La app busca palabras como:

sucursales
nuestras sucursales
casa central
locales
showrooms
Además cuenta menciones a sucursal o local. Si aparecen varias veces, estima branches_estimate >= 2.

Confiabilidad: media.

Por eso dice posible multisucursal. No lo tomaría como 100% confirmado.

Web profesional
La app busca marcas técnicas en el HTML, como:

Shopify
WooCommerce
Tiendanube
VTEX
MercadoShops
Google Tag Manager
Analytics
Confiabilidad: media.

No significa que el negocio sea grande, pero sí que tiene una web más armada.

Negocio físico
Hoy esto se asume por el origen de la búsqueda: Google Maps + rubros físicos.

Confiabilidad: media.

No está validado con una prueba dura. Si querés ser más estricto, podemos cambiarlo para que solo se marque si viene de Google Maps con dirección/teléfono.

Industria ICP
Sale de la industria que vos buscaste o importaste.

Ejemplo: ferreteria, pet shop, repuestera.

Confiabilidad: depende de la búsqueda. Si buscaste “ferretería Córdoba”, se guarda como ferretería.

Canal contactable
Se marca si tiene al menos uno de estos:

email
WhatsApp
Instagram
Confiabilidad: buena como criterio práctico.

No significa que vayan a responder, solo que hay un canal para intentar contacto.

Resumen honesto

Señales más confiables:

Tiene web
Tiene teléfono
Tiene Instagram si hay link real
Tiene WhatsApp si hay link real
Tiene email si aparece en la web
Señales inferidas:

Ecommerce detectado
Stock complejo
Posible multisucursal
Web profesional
Negocio físico