# Guía de Configuración de Firebase

Hola, este archivo explica el método final y correcto para configurar las claves de la aplicación. Para simplificar el proceso y evitar errores de entorno, la configuración ahora se realiza directamente en un archivo de código fuente.

## **Acción Requerida: Configuración Única**

1.  **Abre el archivo:** Navega y abre el archivo `src/firebaseCredentials.ts` en tu editor de código.

2.  **Reemplaza los valores:** Dentro de ese archivo, verás un objeto `firebaseCredentials` con valores de marcador de posición como `"REPLACE_WITH_YOUR_API_KEY"`.

3.  **Pega tu configuración:** Reemplaza todo ese objeto de marcador de posición con el objeto `firebaseConfig` que obtuviste de la consola de Firebase.

**Antes (en `src/firebaseCredentials.ts`):**
```typescript
export const firebaseCredentials = {
  apiKey: "REPLACE_WITH_YOUR_API_KEY",
  authDomain: "REPLACE_WITH_YOUR_AUTH_DOMAIN",
  // ... y así sucesivamente
};
```

**Después (en `src/firebaseCredentials.ts`, usando tu configuración como ejemplo):**
```typescript
export const firebaseCredentials = {
  apiKey: "AIzaSyAbwv...",
  authDomain: "viajes-argentina-en-30-dias.firebaseapp.com",
  projectId: "viajes-argentina-en-30-dias",
  storageBucket: "viajes-argentina-en-30-dias.appspot.com",
  messagingSenderId: "524...",
  appId: "1:52..."
};
```

**Importante:**
-   Solo necesitas pegar el objeto, sin `const firebaseConfig =` al principio ni `;` al final.
-   Una vez que guardes este archivo con tus credenciales reales, la aplicación se conectará a tu proyecto de Firebase automáticamente.

Este método es más directo y elimina cualquier problema relacionado con archivos `.env` o la configuración del entorno de Vercel. **No necesitas configurar ninguna variable de entorno en Vercel con este nuevo sistema.**