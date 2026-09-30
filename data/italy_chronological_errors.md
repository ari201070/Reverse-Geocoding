# Tabla Cronológica de Control y Análisis de Anomalías (Lote Italia - 02 y 03 de Octubre 2023)

Informe de auditoría cronológica estricta sobre el corredor crítico de Octubre 2023 (02/10 y 03/10), exponiendo metadatos reales extraídos en disco vía `ExifDataSuite` y destacando quiebres cinemáticos, puntos ciegos y fallos de OCR/anclaje.

| Archivo | Hora EXIF | Lat/Lng (~4 dec) | ImageDescription | UserComment / H3 | Alerta de Incongruencia |
|---|---|---|---|---|---|
| `IMG-20231002-WA0000.jpeg` | `2023:10:02 08:00:29` | `41.9023, 12.5054` | `Roma` | `Motor Refactorizado v1.0 | H3: 891e8052a27ffff | {...` | Normal |
| `2023-10-02 09.00.58.jpg` | `2023:10:02 09:00:59` | `41.9023, 12.5054` | `Roma` | `Motor Refactorizado v1.0 | H3: 891e8052a27ffff | {...` | Normal |
| `2023-10-02 11.28.01.jpg` | `2023:10:02 11:28:02` | `41.9023, 12.5054` | `Roma` | `Motor Refactorizado v1.0 | H3: 891e8052a27ffff | {...` | Normal |
| `2023-10-02 14.54.11.jpg` | `2023:10:02 14:54:11` | `41.8933, 12.4829` | `Rome` | `Motor Refactorizado v1.0 | H3: 891e8052a27ffff | {...` | Normal |
| `2023-10-02 14.54.16.jpg` | `2023:10:02 14:54:16` | `NULL` | `NULL` | `NULL` | Normal |
| `2023-10-02 14.54.20.jpg` | `2023:10:02 14:54:21` | `41.9023, 12.5054` | `Roma` | `Motor Refactorizado v1.0 | H3: 891e8052a27ffff | {...` | Normal |
| `2023-10-02 14.54.25.jpg` | `2023:10:02 14:54:25` | `NULL` | `NULL` | `NULL` | Normal |
| `2023-10-02 14.55.07.jpg` | `2023:10:02 14:55:08` | `41.9023, 12.5054` | `Roma` | `Motor Refactorizado v1.0 | H3: 891e8052a27ffff | {...` | Normal |
| `2023-10-02 14.58.15.jpg` | `2023:10:02 14:58:15` | `NULL` | `NULL` | `NULL` | Normal |
| `2023-10-02 14.58.17.jpg` | `2023:10:02 14:58:17` | `41.8933, 12.4829` | `Rome` | `Motor Refactorizado v1.0 | H3: 891e8052a27ffff | {...` | Normal |
| `2023-10-02 14.58.20.jpg` | `2023:10:02 14:58:20` | `NULL` | `NULL` | `NULL` | Normal |
| `2023-10-02 14.58.55.jpg` | `2023:10:02 14:58:55` | `43.7698, 11.2556` | `Florence` | `Motor Refactorizado v1.0 | H3: 891e8052a27ffff | {...` | Normal |
| `2023-10-02 14.59.00.jpg` | `2023:10:02 14:59:00` | `43.7698, 11.2556` | `Florence` | `Motor Refactorizado v1.0 | H3: 891e8052a27ffff | {...` | Normal |
| `2023-10-02 16.23.48_IMG_20231002_162348.jpg` | `2023:10:02 16:23:48` | `43.7698, 11.2556` | `Florence` | `Motor Refactorizado v1.0 | H3: 891e8052a27ffff | {...` | Normal |
| `2023-10-02 16.23.58_IMG_20231002_162358.jpg` | `2023:10:02 16:23:58` | `43.7698, 11.2556` | `Florence` | `Motor Refactorizado v1.0 | H3: 891e8052a27ffff | {...` | Normal |
| `2023-10-02 16.24.00_IMG_20231002_162400.jpg` | `2023:10:02 16:24:01` | `43.7698, 11.2556` | `Florence` | `Motor Refactorizado v1.0 | H3: 891e8052a27ffff | {...` | Normal |
| `2023-10-02 16.30.50_IMG_20231002_163050.jpg` | `2023:10:02 16:30:51` | `43.7698, 11.2556` | `Florence` | `Motor Refactorizado v1.0 | H3: 891e8052a27ffff | {...` | Normal |
| `2023-10-02 16.30.52_IMG_20231002_163052.jpg` | `2023:10:02 16:30:52` | `43.7698, 11.2556` | `Florence` | `Motor Refactorizado v1.0 | H3: 891e8052a27ffff | {...` | Normal |
| `2023-10-02 18.50.12_IMG_20231002_185012.jpg` | `2023:10:02 18:50:13` | `43.7698, 11.2556` | `Florence` | `Motor Refactorizado v1.0 | H3: 891e8052a27ffff | {...` | ⚠️ Salto Cuántico 1: Florencia (18:50) -> Salto cinemático inicial |
| `2023-10-02 19.16.01.jpg` | `2023:10:02 19:16:01` | `41.9023, 12.5054` | `Roma` | `Motor Refactorizado v1.0 | H3: 891e8052a27ffff | {...` | ⚠️ Salto Cuántico 2: Roma (19:16) en ráfaga nocturna (Velocidad implausible >230km en 25m) |
| `2023-10-02 19.17.38.jpg` | `2023:10:02 19:17:38` | `43.7698, 11.2556` | `Florence` | `Motor Refactorizado v1.0 | H3: 891e8052a27ffff | {...` | ⚠️ Salto Cuántico 3: Retorno instantáneo a Florencia (19:17) |
| `2023-10-03 08.47.22.jpg` | `2023:10:03 08:47:23` | `41.8933, 12.4829` | `Rome` | `Motor Refactorizado v1.0 | H3: 891e8052a27ffff | {...` | Normal |
| `2023-10-03 08.47.34.jpg` | `2023:10:03 08:47:34` | `41.8933, 12.4829` | `Rome` | `Motor Refactorizado v1.0 | H3: 891e8052a27ffff | {...` | Normal |
| `2023-10-03 09.21.59_IMG_20231003_092159.jpg` | `2023:10:03 09:21:59` | `41.8933, 12.4829` | `Rome` | `Motor Refactorizado v1.0 | H3: 891e8052a27ffff | {...` | Normal |
| `2023-10-03 09.23.13_IMG_20231003_092313.jpg` | `2023:10:03 09:23:13` | `41.8933, 12.4829` | `Rome` | `Motor Refactorizado v1.0 | H3: 891e8052a27ffff | {...` | Normal |
| `2023-10-03 09.24.23.jpg` | `2023:10:03 09:24:23` | `41.8933, 12.4829` | `Rome` | `Motor Refactorizado v1.0 | H3: 891e8052a27ffff | {...` | Normal |
| `2023-10-03 09.25.19_IMG_20231003_092519.jpg` | `2023:10:03 09:25:19` | `41.8933, 12.4829` | `Rome` | `Motor Refactorizado v1.0 | H3: 891e8052a27ffff | {...` | Normal |
| `2023-10-03 09.44.52_IMG_20231003_094452.jpg` | `2023:10:03 09:44:52` | `41.8933, 12.4829` | `Rome` | `Motor Refactorizado v1.0 | H3: 891e8052a27ffff | {...` | Normal |
| `2023-10-03 09.47.47_IMG_20231003_094747.jpg` | `2023:10:03 09:47:48` | `41.8933, 12.4829` | `Rome` | `Motor Refactorizado v1.0 | H3: 891e8052a27ffff | {...` | Normal |
| `2023-10-03 09.47.53_IMG_20231003_094753.jpg` | `2023:10:03 09:47:53` | `41.9023, 12.5054` | `Rome` | `Motor Refactorizado v1.0 | H3: 891e8052a27ffff | {...` | Normal |
| `2023-10-03 09.50.51_IMG_20231003_095051.jpg` | `2023:10:03 09:50:51` | `41.8933, 12.4829` | `Rome` | `Motor Refactorizado v1.0 | H3: 891e8052a27ffff | {...` | Normal |
| `2023-10-03 09.50.54_IMG_20231003_095054.jpg` | `2023:10:03 09:50:54` | `41.8933, 12.4829` | `Rome` | `Motor Refactorizado v1.0 | H3: 891e8052a27ffff | {...` | Normal |
| `2023-10-03 09.51.01_IMG_20231003_095101.jpg` | `2023:10:03 09:51:01` | `41.9023, 12.5054` | `Rome` | `Motor Refactorizado v1.0 | H3: 891e8052a27ffff | {...` | Normal |
| `2023-10-03 09.51.22_IMG_20231003_095122.jpg` | `2023:10:03 09:51:23` | `41.8933, 12.4829` | `Rome` | `Motor Refactorizado v1.0 | H3: 891e8052a27ffff | {...` | Normal |
| `2023-10-03 09.51.38_IMG_20231003_095138.jpg` | `2023:10:03 09:51:38` | `41.8933, 12.4829` | `Rome` | `Motor Refactorizado v1.0 | H3: 891e8052a27ffff | {...` | Normal |
| `2023-10-03 09.51.40_IMG_20231003_095140.jpg` | `2023:10:03 09:51:41` | `41.9023, 12.5054` | `Rome` | `Motor Refactorizado v1.0 | H3: 891e8052a27ffff | {...` | Normal |
| `2023-10-03 09.52.06_IMG_20231003_095206.jpg` | `2023:10:03 09:52:06` | `41.8933, 12.4829` | `Rome` | `Motor Refactorizado v1.0 | H3: 891e8052a27ffff | {...` | Normal |
| `2023-10-03 09.52.57_IMG_20231003_095257.jpg` | `2023:10:03 09:52:58` | `41.8933, 12.4829` | `Rome` | `Motor Refactorizado v1.0 | H3: 891e8052a27ffff | {...` | Normal |
| `2023-10-03 09.53.16_IMG_20231003_095316.jpg` | `2023:10:03 09:53:16` | `41.9023, 12.5054` | `Rome` | `Motor Refactorizado v1.0 | H3: 891e8052a27ffff | {...` | Normal |
| `2023-10-03 09.53.20_IMG_20231003_095320.jpg` | `2023:10:03 09:53:21` | `41.8933, 12.4829` | `Rome` | `Motor Refactorizado v1.0 | H3: 891e8052a27ffff | {...` | Normal |
| `2023-10-03 09.53.29.jpg` | `2023:10:03 09:53:29` | `41.8933, 12.4829` | `Rome` | `Motor Refactorizado v1.0 | H3: 891e8052a27ffff | {...` | Normal |
| `2023-10-03 09.53.37.jpg` | `2023:10:03 09:53:37` | `41.8933, 12.4829` | `Rome` | `Motor Refactorizado v1.0 | H3: 891e8052a27ffff | {...` | Normal |
| `2023-10-03 09.53.52.jpg` | `2023:10:03 09:53:52` | `41.8933, 12.4829` | `Rome` | `Motor Refactorizado v1.0 | H3: 891e8052a27ffff | {...` | Normal |
| `2023-10-03 09.55.19_IMG_20231003_095519.jpg` | `2023:10:03 09:55:19` | `41.8933, 12.4829` | `Rome` | `Motor Refactorizado v1.0 | H3: 891e8052a27ffff | {...` | Normal |
| `2023-10-03 09.56.15.jpg` | `2023:10:03 09:56:15` | `41.8933, 12.4829` | `Rome` | `Motor Refactorizado v1.0 | H3: 891e8052a27ffff | {...` | Normal |
| `2023-10-03 09.56.34_IMG_20231003_095634.jpg` | `2023:10:03 09:56:34` | `41.8933, 12.4829` | `Rome` | `Motor Refactorizado v1.0 | H3: 891e8052a27ffff | {...` | Normal |
| `2023-10-03 09.56.38_IMG_20231003_095638.jpg` | `2023:10:03 09:56:38` | `41.8933, 12.4829` | `Rome` | `Motor Refactorizado v1.0 | H3: 891e8052a27ffff | {...` | Normal |
| `2023-10-03 09.56.41_IMG_20231003_095641.jpg` | `2023:10:03 09:56:41` | `41.8933, 12.4829` | `Rome` | `Motor Refactorizado v1.0 | H3: 891e8052a27ffff | {...` | Normal |
| `2023-10-03 09.57.00_IMG_20231003_095700.jpg` | `2023:10:03 09:57:00` | `41.8933, 12.4829` | `Rome` | `Motor Refactorizado v1.0 | H3: 891e8052a27ffff | {...` | Normal |
| `2023-10-03 09.58.00_IMG_20231003_095800.jpg` | `2023:10:03 09:58:00` | `41.9023, 12.5054` | `Rome` | `Motor Refactorizado v1.0 | H3: 891e8052a27ffff | {...` | Normal |
| `2023-10-03 09.58.05_IMG_20231003_095805.jpg` | `2023:10:03 09:58:05` | `NULL` | `NULL` | `NULL` | 🚨 Punto Ciego / Ráfaga Ciega: Datos GPS y descriptivos NULL (vacío físico) |
| `2023-10-03 09.59.21_IMG_20231003_095921.jpg` | `2023:10:03 09:59:21` | `NULL` | `NULL` | `NULL` | Normal |
| `2023-10-03 09.59.27_IMG_20231003_095927.jpg` | `2023:10:03 09:59:27` | `NULL` | `NULL` | `NULL` | Normal |
| `2023-10-03 10.07.44_IMG_20231003_100744.jpg` | `2023:10:03 10:07:44` | `NULL` | `NULL` | `NULL` | Normal |
| `2023-10-03 10.07.49_IMG_20231003_100749.jpg` | `2023:10:03 10:07:49` | `NULL` | `NULL` | `NULL` | Normal |
| `2023-10-03 10.14.08_IMG_20231003_101408.jpg` | `2023:10:03 10:14:08` | `NULL` | `NULL` | `NULL` | Normal |
| `2023-10-03 10.15.11_IMG_20231003_101511.jpg` | `2023:10:03 10:15:12` | `NULL` | `NULL` | `NULL` | Normal |
| `2023-10-03 10.25.05_IMG_20231003_102505.jpg` | `2023:10:03 10:25:05` | `NULL` | `NULL` | `NULL` | 🚨 Fallo de OCR / Lectura de Panel: Santa María la Mayor sin metadatos descriptivos (NULL) |
| `2023-10-03 10.30.52.jpg` | `2023:10:03 10:30:52` | `43.0470, 11.8441` | `Roma` | `Motor Refactorizado v1.0 | H3: 891e84c43afffff | {...` | Normal |
| `2023-10-03 10.30.56.jpg` | `2023:10:03 10:30:56` | `43.0470, 11.8441` | `Roma` | `Motor Refactorizado v1.0 | H3: 891e84c43afffff | {...` | Normal |
| `2023-10-03 10.56.45_IMG_20231003_105645.jpg` | `2023:10:03 10:56:45` | `NULL` | `NULL` | `NULL` | Normal |
| `2023-10-03 12.27.53.jpg` | `2023:10:03 12:27:53` | `43.0470, 11.8441` | `Roma` | `Motor Refactorizado v1.0 | H3: 891e84c43afffff | {...` | Normal |
| `2023-10-03 12.32.33.jpg` | `2023:10:03 12:32:33` | `43.0470, 11.8441` | `Roma` | `Motor Refactorizado v1.0 | H3: 891e84c43afffff | {...` | Normal |
| `2023-10-03 15.24.41_IMG_20231003_152441.jpg` | `2023:10:03 15:24:42` | `NULL` | `NULL` | `NULL` | Normal |
| `2023-10-03 15.27.43_IMG_20231003_152743.jpg` | `2023:10:03 15:27:43` | `NULL` | `NULL` | `NULL` | Normal |
| `2023-10-03 15.27.48_IMG_20231003_152748.jpg` | `2023:10:03 15:27:49` | `NULL` | `NULL` | `NULL` | Normal |
| `2023-10-03 15.28.30_IMG_20231003_152830.jpg` | `2023:10:03 15:28:30` | `NULL` | `NULL` | `NULL` | Normal |
| `2023-10-03 15.31.22_IMG_20231003_153122.jpg` | `2023:10:03 15:31:22` | `NULL` | `NULL` | `NULL` | Normal |
| `2023-10-03 15.36.09_IMG_20231003_153609.jpg` | `2023:10:03 15:36:09` | `NULL` | `NULL` | `NULL` | Normal |
| `2023-10-03 15.36.18_IMG_20231003_153618.jpg` | `2023:10:03 15:36:19` | `NULL` | `NULL` | `NULL` | Normal |
| `2023-10-03 15.36.24_IMG_20231003_153624.jpg` | `2023:10:03 15:36:24` | `NULL` | `NULL` | `NULL` | Normal |
| `2023-10-03 15.36.49_IMG_20231003_153649.jpg` | `2023:10:03 15:36:49` | `NULL` | `NULL` | `NULL` | Normal |
| `2023-10-03 15.39.25_IMG_20231003_153925.jpg` | `2023:10:03 15:39:25` | `NULL` | `NULL` | `NULL` | Normal |
| `2023-10-03 15.41.44_IMG_20231003_154144.jpg` | `2023:10:03 15:41:45` | `NULL` | `NULL` | `NULL` | Normal |
| `2023-10-03 15.41.55.jpg` | `2023:10:03 15:41:55` | `43.0470, 11.8441` | `Roma` | `Motor Refactorizado v1.0 | H3: 891e84c43afffff | {...` | Normal |
| `2023-10-03 15.56.50.jpg` | `2023:10:03 15:56:50` | `43.0470, 11.8441` | `Roma` | `Motor Refactorizado v1.0 | H3: 891e84c43afffff | {...` | Normal |
| `2023-10-03 16.00.46_IMG_20231003_160046.jpg` | `2023:10:03 16:00:46` | `NULL` | `NULL` | `NULL` | Normal |
| `2023-10-03 16.01.04_IMG_20231003_160104.jpg` | `2023:10:03 16:01:04` | `NULL` | `NULL` | `NULL` | Normal |
| `2023-10-03 16.01.32_IMG_20231003_160132.jpg` | `2023:10:03 16:01:33` | `NULL` | `NULL` | `NULL` | Normal |
| `2023-10-03 16.01.42_IMG_20231003_160142.jpg` | `2023:10:03 16:01:42` | `NULL` | `NULL` | `NULL` | Normal |
| `2023-10-03 16.03.07_IMG_20231003_160307.jpg` | `2023:10:03 16:03:07` | `NULL` | `NULL` | `NULL` | Normal |
| `2023-10-03 16.03.13_IMG_20231003_160313.jpg` | `2023:10:03 16:03:14` | `NULL` | `NULL` | `NULL` | Normal |
| `2023-10-03 16.10.56_IMG_20231003_161056.jpg` | `2023:10:03 16:10:56` | `NULL` | `NULL` | `NULL` | Normal |
| `2023-10-03 16.12.56_IMG_20231003_161256.jpg` | `2023:10:03 16:12:57` | `NULL` | `NULL` | `NULL` | Normal |
| `2023-10-03 16.13.34_IMG_20231003_161334.jpg` | `2023:10:03 16:13:34` | `NULL` | `NULL` | `NULL` | Normal |
| `2023-10-03 16.13.34_IMG_20231003_Musei Vaticani.jpg` | `2023:10:03 16:13:34` | `43.0470, 11.8441` | `Roma` | `Motor Refactorizado v1.0 | H3: 891e84c43afffff | {...` | Normal |
| `2023-10-03 16.15.16_IMG_20231003_161516.jpg` | `2023:10:03 16:15:16` | `NULL` | `NULL` | `NULL` | Normal |
| `2023-10-03 16.17.38_IMG_20231003_161738.jpg` | `2023:10:03 16:17:38` | `NULL` | `NULL` | `NULL` | Normal |
| `2023-10-03 16.20.49_IMG_20231003_162049.jpg` | `2023:10:03 16:20:50` | `NULL` | `NULL` | `NULL` | Normal |
| `2023-10-03 16.59.24_IMG_20231003_165924.jpg` | `2023:10:03 16:59:24` | `NULL` | `NULL` | `NULL` | Normal |
| `2023-10-03 16.59.28_IMG_20231003_165928.jpg` | `2023:10:03 16:59:28` | `NULL` | `NULL` | `NULL` | Normal |
| `2023-10-03 16.59.38_IMG_20231003_165938.jpg` | `2023:10:03 16:59:38` | `NULL` | `NULL` | `NULL` | Normal |
| `2023-10-03 17.02.17_IMG_20231003_170217.jpg` | `2023:10:03 17:02:17` | `NULL` | `NULL` | `NULL` | Normal |
| `2023-10-03 17.02.20_IMG_20231003_170220.jpg` | `2023:10:03 17:02:20` | `NULL` | `NULL` | `NULL` | Normal |
| `2023-10-03 17.07.51_IMG_20231003_170751.jpg` | `2023:10:03 17:07:51` | `NULL` | `NULL` | `NULL` | Normal |
| `2023-10-03 17.10.34_IMG_20231003_171034.jpg` | `2023:10:03 17:10:34` | `NULL` | `NULL` | `NULL` | Normal |
| `2023-10-03 17.19.20_IMG_20231003_171920.jpg` | `2023:10:03 17:19:20` | `NULL` | `NULL` | `NULL` | Normal |
| `2023-10-03 17.19.33_IMG_20231003_171933.jpg` | `2023:10:03 17:19:33` | `NULL` | `NULL` | `NULL` | Normal |
| `2023-10-03 17.19.36_IMG_20231003_171936.jpg` | `2023:10:03 17:19:36` | `NULL` | `NULL` | `NULL` | Normal |
| `2023-10-03 17.20.37.jpg` | `2023:10:03 17:20:37` | `43.0470, 11.8441` | `Roma` | `Motor Refactorizado v1.0 | H3: 891e84c43afffff | {...` | Normal |
| `2023-10-03 17.20.53.jpg` | `2023:10:03 17:20:53` | `43.0470, 11.8441` | `Roma` | `Motor Refactorizado v1.0 | H3: 891e84c43afffff | {...` | Normal |
| `2023-10-03 17.21.19.jpg` | `2023:10:03 17:21:21` | `NULL` | `NULL` | `NULL` | Normal |
| `2023-10-03 17.22.06.jpg` | `2023:10:03 17:22:06` | `43.0470, 11.8441` | `Roma` | `Motor Refactorizado v1.0 | H3: 891e84c43afffff | {...` | Normal |
| `2023-10-03 17.22.13.jpg` | `2023:10:03 17:22:13` | `43.0470, 11.8441` | `Roma` | `Motor Refactorizado v1.0 | H3: 891e84c43afffff | {...` | Normal |
| `2023-10-03 17.22.15.jpg` | `2023:10:03 17:22:15` | `43.0470, 11.8441` | `Roma` | `Motor Refactorizado v1.0 | H3: 891e84c43afffff | {...` | Normal |
| `2023-10-03 17.22.36.jpg` | `2023:10:03 17:22:36` | `43.0470, 11.8441` | `Roma` | `Motor Refactorizado v1.0 | H3: 891e84c43afffff | {...` | Normal |
| `2023-10-03 17.23.59_IMG_20231003_172359.jpg` | `2023:10:03 17:23:59` | `NULL` | `NULL` | `NULL` | Normal |
| `2023-10-03 17.30.24_IMG_20231003_173024.jpg` | `2023:10:03 17:30:24` | `NULL` | `NULL` | `NULL` | Normal |
| `2023-10-03 17.40.24.jpg` | `2023:10:03 17:40:24` | `41.9069, 12.4533` | `Rome` | `Motor Refactorizado v1.0 | H3: 891e80505d7ffff | {...` | Normal |
| `2023-10-03 18.22.35_IMG_20231003_182235.jpg` | `2023:10:03 18:22:35` | `NULL` | `NULL` | `NULL` | Normal |
| `2023-10-03 18.23.52.jpg` | `2023:10:03 18:23:53` | `41.8933, 12.4829` | `Roma` | `Motor Refactorizado v1.0 | H3: 891e8052a4bffff | {...` | Normal |
| `2023-10-03 18.24.39.jpg` | `2023:10:03 18:24:39` | `41.9069, 12.4533` | `Roma` | `Motor Refactorizado v1.0 | H3: 891e80505d7ffff | {...` | Normal |
| `2023-10-03 18.24.48.jpg` | `2023:10:03 18:24:48` | `41.9069, 12.4533` | `Roma` | `Motor Refactorizado v1.0 | H3: 891e80505d7ffff | {...` | Normal |
| `2023-10-03 18.25.07.jpg` | `2023:10:03 18:25:07` | `41.9069, 12.4533` | `Roma` | `Motor Refactorizado v1.0 | H3: 891e80505d7ffff | {...` | Normal |
| `2023-10-03 18.25.29.jpg` | `2023:10:03 18:25:29` | `41.9069, 12.4533` | `Roma` | `Motor Refactorizado v1.0 | H3: 891e80505d7ffff | {...` | Normal |
| `2023-10-03 18.31.23_IMG_20231003_183123.jpg` | `2023:10:03 18:31:23` | `NULL` | `NULL` | `NULL` | Normal |
| `2023-10-03 18.31.29_IMG_20231003_183129.jpg` | `2023:10:03 18:31:29` | `NULL` | `NULL` | `NULL` | Normal |