# CloudFront HTTPS Workaround (Mixed Content Fix)

**Contexto:** El Frontend alojado en AWS Amplify se sirve a través de HTTPS. Por reglas de seguridad de los navegadores web, una aplicación HTTPS no puede realizar peticiones a un endpoint HTTP (Mixed Content). Nuestro Application Load Balancer (ALB) expone HTTP en el puerto 80. Para asignarle un certificado HTTPS al ALB desde AWS Certificate Manager (ACM), se requiere la validación de un dominio propio comprado.

**Decisión:** Como se trata de un MVP y no se cuenta con dominio propio, se utiliza **Amazon CloudFront** como proxy inverso (Reverse Proxy) frente al ALB.

**Por qué:** CloudFront provee un dominio genérico con certificado SSL válido (`https://dXXXXXX.cloudfront.net`) de forma gratuita. Puede conectarse al ALB utilizando HTTP como protocolo de origen. Esto enmascara el tráfico HTTP permitiendo al frontend en Amplify consumir la API a través de HTTPS de forma segura, evadiendo los bloqueos del navegador.

**Consecuencias / Implementación:**
- Se debe aprovisionar manualmente una distribución de CloudFront apuntando al CfnOutput `AlbDnsName`.
- Las políticas de caché de CloudFront deben deshabilitarse (`CachingDisabled`) y debe reenviar todos los headers (`AllViewer`) para no romper la autenticación JWT ni el CORS.
- La variable `VITE_API_URL` en Amplify debe apuntar a la URL de CloudFront, no al ALB.

**Reversibilidad:** Alta. Cuando el proyecto adquiera un dominio propio (ej. `blendx.com`), se puede generar un certificado en ACM, adjuntarlo directamente al ALB para habilitar HTTPS nativo, y eliminar la distribución de CloudFront sin afectar la lógica de la aplicación.
