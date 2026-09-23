# Informe Auditoria Calidad Vouchers - OCR Visual y Guardrails

**Total vouchers re-procesados:** 124 (`data/vouchers/2026-09/`)
**Criterio OCR visual:** capa texto <100 chars o `startDate`/`location` null -> conversion a imagen + OCR Qwen2.5-VL / PaddleOCR
**Moneda Europa:** vouchers Italia/Europa forzados a `EUR` (prohibido `ARS`)
**Guardrail:** si `place` detectado y `startDate` o `coordinates` null -> `FAIL`/`EXTRACTION_FAILED`

| Archivo Voucher | Lugar Extraido | Fecha y Hora | Coordenadas / H3 | Moneda | Estado |
|---|---|---|---|---|---|
| 2010-07-04 21.09.14_mapofmontenegro_big. | Hotel Actual | null | null | null | FAIL |
| 20251021_183644.heic | Hotel Actual | null | null | null | FAIL |
| 24009-אריאל פליאר.pdf | Esteriω | 2023-04-08 | -21.4692,-47.0019 / 89a8adac22 | ARS | PASS |
| 24117 - אריאל פליאר - G3211.pdf | OHH Eur - אוצר החייל Eur | 2023-03-29 06:37 | null | EUR | FAIL |
| 5737_20251102_251202_130522.pdf | 5737_20251102_251202_130522 | 2025-12-31 | null | USD | FAIL |
| 6691122.pdf | 6691122 | null | null | USD | FAIL |
| ARIEL RUBEN FLIER.pdf | Addis Ababa, Bole International | null 01:00 | 8.9792,38.7966 / 89529b79213ff | ARS | FAIL |
| Aeropuerto_hotel.pdf | Rome Termini via Giolitti | 2023-09-30 00:00 | 41.8987,12.5036 / 891e8052a2ff | EUR | PASS |
| Ari-Pas.jpeg | Hotel Actual | null | null | null | FAIL |
| Ari_NTTZSH47_251007_180046.pdf | Mendoza | 2025-10-10 13:00 | -34.597,-68.7305 / 89b2eb7949b | ARS | PASS |
| Arkia2ways_11036968.pdf | Eilat Ramon Airport | null 06:30 | 29.7266,35.0061 / 893e68981aff | ARS | FAIL |
| B&B Marbò Florence_ אישור.pdf | B&B Marbò Florence | 2023-10-05 13:30 | null | EUR | FAIL |
| BIH 2304 טבלת מלונות וטיסות עבור אריאל פ | Skenderija 1 | null 08:25 | 44.5058,19.5452 / 891ef4a2087f | EUR | FAIL |
| BIH 2304 לבוסניה-הרצגובינה טקסט טיול 2 T | BIH 2304 לבוסניה-הרצגובינה טקסט טיול 2 T | null | null | EUR | FAIL |
| BIH 2304 לבוסניה-הרצגובינה טקסט טיול 2 ע | BIH 2304 לבוסניה-הרצגובינה טקסט טיול 2 ע | null | null | EUR | FAIL |
| BLeumi_20221218152738_69956142_TeudatNec | SUSANA RUTH FLIER | 2029-09-28 19:30 | null | ARS | FAIL |
| Boarding pass.pdf | LIRAN | 2023-10-02 11:30 | 32.6475,54.5644 / 89432c0d0cbf | ARS | PASS |
| Boardingpass_IZ802.pdf | Zone C | null 06:50 | -15.2569,39.2508 / 8997b52cc6f | ARS | FAIL |
| Booking_Argentina_2025_Hoteles.png | Hotel Actual | null | null | null | FAIL |
| Booking_Argentina_2025_Traslado.png | Hotel Actual | null | null | null | FAIL |
| Booking_BuenosAires_2011_HotelMundial.pn | Booking_BuenosAires_2011_HotelMundial.pn | null | null | null | FAIL |
| Booking_Italia_2023_Hoteles.png | Hotel Italia | 2023-04-15 | null | EUR | FAIL |
| Booking_Slovenia_2015_ApartmentsZorc.png | Booking_Slovenia_2015_ApartmentsZorc.png | null | null | null | FAIL |
| Booking_Slovenia_2015_GarniHotelAzur.png | Hotel Actual | null | null | null | FAIL |
| Booking_Slovenia_2015_HotelKrim.png | Booking_Slovenia_2015_HotelKrim.png | null | null | null | FAIL |
| Booking_Slovenia_2015_HotelSavica.png | Hotel Actual | null | null | null | FAIL |
| Brc-Mza.pdf | MENDOZA | 2025-10-11 13:00 | -34.597,-68.7305 / 89b2eb7949b | ARS | PASS |
| BsAs-Ros.jpg | Hotel Actual | null | null | null | FAIL |
| CAR RENTAL VOUCHER.pdf | CAR RENTAL VOUCHER | null 21:30 | null | USD | FAIL |
| Capilla Sixtina y los Museos Vaticanos.p | Viale Vaticano, 95, 00192 Roma RM, Itali | 2023-10-01 14:30 | 41.9074,12.455 / 891e805058bff | EUR | PASS |
| CheckMyTrip-1.pdf | CheckMyTrip-1 | null | null | null | FAIL |
| Colosseum, Forum, and Palatine Hill Tour | Arch of Constantine | null 02:30 | 41.8898,12.4907 / 891e80501a7f | EUR | FAIL |
| Confirmación_Fuente Mayor Hotel Centro.p | Fuente Mayor Hotel Centro | null 10:00 | null | USD | FAIL |
| Confirmation690546-1.pdf | Calma Spa | 2025-01-13 08:00 | 39.5378,2.457 / 89394260203fff | Shekel | PASS |
| Confirmation690911-1.pdf | Calmaspa | 2025-01-12 12:00 | null | Shekel | FAIL |
| Ctes.BsAs_WO9L7869_251014_154040.pdf | Ctes.BsAs_WO9L7869_251014_154040 | 2025-10-14 16:00 | null | USD | FAIL |
| DWAM-6656431.pdf | Wizz Air Malta Limited | 2023-10-16 | null | EUR | FAIL |
| E-Ticket.pdf | MUNICH MUC | 2021-11-15 | 48.0919,11.5242 / 891f8d7b4abf | ARS | PASS |
| Electronic ticket receipt, September 15  | TERMINAL 3 | null 08:25 | -6.1199,106.6651 / 898c106d68f | null | FAIL |
| ExitStatement1.pdf | ישראל | 2021-11-17 18:47 | 30.8124,34.8595 / 893e6c86147f | ARS | PASS |
| Fiumicino Airport to Rome Termini.pdf | Rome Termini via Giolitti | 2023-10-02 00:00 | 41.8987,12.5036 / 891e8052a2ff | EUR | PASS |
| Foss - Israeli customer convention (005) | Hillerod Hotel | 2021-07-12 18:15 | 55.9319,12.2975 / 891f232a6b7f | ARS | PASS |
| HILA FLIER.pdf | Addis Ababa, Bole International | null 09:05 | 8.9792,38.7966 / 89529b79213ff | ARS | FAIL |
| Hila-Pas.jpeg | Hila-Pas.jpeg | null | null | null | FAIL |
| Hila_NTTZSH47.pdf | San Carlos de Bariloche - Mendoza | 2025-10-10 13:00 | -41.1343,-71.281 / 89ce80b3143 | ARS | PASS |
| Hotel Soperga_ אישור.pdf | Hotel Soperga | 2019-10-12 14:00 | null | EUR | FAIL |
| LIRAN FLIER.pdf | Addis Ababa, Bole International | null 00:15 | 8.9792,38.7966 / 89529b79213ff | ARS | FAIL |
| Liran-Pas.jpeg | Hotel Actual | null | null | null | FAIL |
| Liran_NTTZSH47.pdf | Mendoza | 2025-10-10 13:00 | -34.597,-68.7305 / 89b2eb7949b | ARS | PASS |
| Miran.jpg | Miran.jpg | null | null | null | FAIL |
| Montenegro-06.2010.pdf | דוברובניק | null | 42.6491,18.094 / 891e8db42b7ff | USD | FAIL |
| Museo Leonardo da Vinci.pdf | Mostra di Leonardo Da Vinci | null 10:00 | null | EUR | FAIL |
| Pantheon.pdf | Piazza Navona, 25 | null 11:30 | 41.8991,12.4728 / 891e8050523f | EUR | FAIL |
| Pasaporte.jpg | Pasaporte.jpg | null | null | null | FAIL |
| Reference number-80005684.pdf | Best Western Hotel Hillerød | null 18:30 | null | ARS | FAIL |
| Res4122467.pdf | קרית שלמה, צריפין 377 | 2021-12-01 12:00 | null | ARS | FAIL |
| Ryanair_אישור טיסה.pdf | Tel Aviv to Rome Fiumicino | 2023-10-02 11:30 | null | EUR | FAIL |
| SHOSHANA FLIER.pdf | Addis Ababa, Bole International | null 01:00 | 8.9792,38.7966 / 89529b79213ff | ARS | FAIL |
| Shoshi-Pas.jpeg | Hotel Actual | null | null | null | FAIL |
| Shoshi_NTTZSH47.pdf | Mendoza | 2025-10-11 07:00 | -34.597,-68.7305 / 89b2eb7949b | ARS | PASS |
| Sincerandome.pdf | En definitiva, fuera de lo exterior (que | null | null | null | FAIL |
| Sun Moon_ אישור.pdf | Sun Moon | 2022-10-13 13:00 | 35.7507,139.7496 / 892f5a30c2b | EUR | PASS |
| Sun Moon_חדש אישור.pdf | Sun Moon | 2023-10-17 12:00 | 35.7507,139.7496 / 892f5a30c2b | ARS | PASS |
| Sun Moon_מבוטלת.pdf | Sun Moon | 2023-09-28 17:00 | 35.7507,139.7496 / 892f5a30c2b | ARS | PASS |
| Ticket Viator-Ariel Flier-BR-1069568671_ | Viale Vaticano, 95, Viale Vaticano, 95,  | null 14:30 | 41.9074,12.455 / 891e805058bff | EUR | FAIL |
| Travel Reservation September 15 for MR A | COPENHAGEN, DENMARK | null 13:30 | 55.6867,12.5701 / 891f058318ff | ARS | FAIL |
| Trip Print _ TripIt.pdf | Via Palestro, 49, 00185 Roma RM, Italy | 2023-02-10 03:05 | null | EUR | FAIL |
| ZERCRG.pdf | Italo - Nuovo Trasporto Viaggiatori S.p. | null 10:40 | null | EUR | FAIL |
| ari_flier_22218869_33805559.pdf | Ud. viaja por: | 2025-09-30 13:30 | null | null | FAIL |
| boarding-pass-Y0HBMB59-1.pdf | Salta to Puerto Iguazü | 2025-10-19 14:00 | -25.5987,-54.5883 / 89a95ed125 | ARS | PASS |
| caa75838-6d84-44e2-b158-1f018076a2fb_sig | Pilat Ariel | 2025-01-27 12:01 | null | ARS | FAIL |
| complaintAboutTourismServices@tourism.go | ביקורת או בתלונה אתלהה ׳הוד ײיפובא קיבבה | 2023-07-06 15:42 | null | ARS | FAIL |
| constancia-cuil.pdf | constancia-cuil | 2025-09-20 09:07 | null | USD | FAIL |
| files_circulars_food_Food_05-008.pdf | files_circulars_food_Food_05-008 | null | null | null | FAIL |
| global-services-phone-numbers_230925_173 | Vatican City State | null | 41.9034,12.4529 / 891e80505c7f | ARS | FAIL |
| harel_308667088_13-9-58.pdf | אירופה | 2023-04-29 | 32.0408,34.7513 / 892db0cd5a3f | ARS | PASS |
| herramientas-IA-Version2-0-joaquin-barbe | LEONARDO AI: Modelo de generación de imá | null | null | null | FAIL |
| hila_flier_22218869_33805561.pdf | Ud. viaja por: | 2025-09-30 13:30 | null | null | FAIL |
| itinerary_Y0HBMB59-1.pdf | Salta → Iguazu | 2025-10-14 14:00 | -23.1556,-64.3185 / 89b3429530 | ILS | PASS |
| itinp11036968 (002).html.pdf | Tel Aviv Ramon Airport | null 15:14 | null | ARS | FAIL |
| liran_flier_22218869_33805560.pdf | Ud. viaja por: | 2025-09-30 13:30 | null | null | FAIL |
| mza-salta.pdf | mza-salta | 2025-10-14 13:00 | -32.8832,-68.8339 / 89b2eea183 | USD | PASS |
| natbag_601575590o.Pdf | אינטרספייס בע | 2021-12-09 13:04 | null | USD | FAIL |
| pdf24-Trip Print _ TripIt.pdf | Viale Vaticano, 84, 00165 Roma RM, Italy | 2023-10-02 10:00 | 41.9074,12.455 / 891e805058bff | EUR | PASS |
| qrcode_www.lefrecce.it.png | qrcode_www.lefrecce.it.png | null | null | null | FAIL |
| shoshi_flier_22218869_33805558.pdf | Ud. viaja por: | 2025-09-30 13:30 | null | null | FAIL |
| ticket (1).pdf | Buenos Aires Ministro Pistarini Airport | null 20:25 | -34.8168,-58.5474 / 89c2e3833d | ARS | FAIL |
| ticket.pdf | Ben Gurion | null 01:00 | 32.0909,34.8234 / 892db0cca87f | USD | FAIL |
| ticket.pdf | Ben Gurion Airport, Terminal 3 | null 01:00 | null | USD | FAIL |
| ticket.pdf | Buenos Aires Ministro Pistarini Airport | 2025-10-28 21:30 | -34.8168,-58.5474 / 89c2e3833d | USD | PASS |
| ticket_NTTZSH47.pdf | Mendoza | 2025-10-10 13:00 | -34.597,-68.7305 / 89b2eb7949b | ARS | PASS |
| transaction_NTTZSH47.pdf | transaction_NTTZSH47 | 2025-10-05 13:47 | null | null | FAIL |
| vouchersBest Western Hotel Hillerod-Hill | Best Western Hotel Hillerod | 2024-09-16 00:00 | null | DKK | FAIL |
| vouchersHotel Astoria Bw Signature Colle | Hotel Astoria Bw Signature Collection | null | null | null | FAIL |
| vouchersHotel Astoria Bw Signature Colle | Hotel Astoria Bw Signature Collection | 2024-08-20 00:00 | null | ARS | FAIL |
| yd_conf_heb_pt2318803732.pdf | yd_conf_heb_pt2318803732 | null | null | null | FAIL |
| אישור בדיקת קורונה לחו_ל מבתי חולים.pdf | Yoseftal Medical Center | null 12:42 | 32.0795,34.8815 / 892db05608ff | null | FAIL |
| בדיקה לרשיון נהיגה.pdf | Parque 3 de Febrero | 2023-03-21 10:00 | -32.9515,-60.6466 / 89c2eba310 | ARS | PASS |
| ביטוח לאיטליה.pdf | ביטוח לאיטליה | null | null | null | FAIL |
| בלנדר מוט.pdf | אילת-ביג 232 | null 09:00 | null | ARS | FAIL |
| בקשה להוצאה רישיון נהיגה.pdf | בקשה להוצאה רישיון נהיגה | 2024-04-09 | null | USD | FAIL |
| דוח אריאל פליאר.pdf | Pliar Rubin Ariel | 2010-12-30 | null | ₪ | FAIL |
| דפי מידע - לשכות בריאות איזוריות 1 עבור  | דפי מידע - לשכות בריאות איזוריות 1 עבור  | null | null | null | FAIL |
| דרקון לירן.jpg | דרקון לירן.jpg | null | null | null | FAIL |
| העברת בנקאית 24117 - אריאל פליאר - G3211 | Adama - Tours & Travel Ltd | 2023-03-29 06:37 | null | EUR | FAIL |
| הצהרת יציאה מישראל.pdf | ישראל | 2021-12-06 07:34 | 30.8124,34.8595 / 893e6c86147f | ARS | PASS |
| כניסה לארץ.pdf | Ben Gurion | 2021-12-09 02:50 | 32.0909,34.8234 / 892db0cca87f | USD | PASS |
| לוגו אוטובוס.jpg | Hotel Actual | null | null | null | FAIL |
| מפגש בשדה התעופה עבור אריאל פליאר.pdf | BenGurion | 2023-04-29 08:25 | null | ARS | FAIL |
| מפה.pdf | Parque Tres de Febrero | 2023-03-15 14:00 | -38.3766,-60.2762 / 89c22c4760 | ARS | PASS |
| מפות _Google__.pdf | מפות _Google__ | null | null | USD | FAIL |
| מקדמה 23847 - אריאל פליאר - G3211.pdf | אדמה | 2023-02-09 16:24 | 8.544,39.2705 / 897aca04a4ffff | ש | PASS |
| מקדמה- אריאל פליאר - G3211.pdf | Aerol’i | 2023-02-09 16:24 | null | ARS | FAIL |
| נתבג_כ.מכ'.pdf | טרמינל ארהב הן תל ן ב רב ויג היזטו, ׹יגה | 2021-12-07 20:04 | null | ARS | FAIL |
| סדנת בשרים ובירה.pdf | סדנת בשרים ובירה | null | null | USD | FAIL |
| סלטה ← יגואזו_Y0HBMB59_251014_162748.pdf | סלטה ← יגואזו_Y0HBMB59_251014_162748 | 2025-10-14 14:00 | null | USD | FAIL |
| ספח תעודת זהות דיגיטלי-לירן.pdf | Hotel Sheraton Buenos Aires | 2023-03-15 20:00 | -38.0317,-57.5399 / 89c20360d4 | ARS | PASS |
| פוליסת ביטוח הראל.pdf | פוליסת ביטוח הראל | 2023-04-03 | null | USD | FAIL |
| קבלה כרטיסי טיסה_1.pdf | Shoshana Flier | 2025-08-26 28:43 | null | ₪ | FAIL |
| רשימת ציוד.pdf | יוד | null 19:14 | 36.1386,139.4559 / 892e749502b | ARS | PASS |
| רשימת קשר  - BIH 2304 לבוסניה והרצוגובינ | לבוסניה והרצוגובינה | null | null | EUR | FAIL |
| תדפיס הזמנת מלון  - 4300080795.pdf | תדפיס הזמנת מלון  - 4300080795 | 2024-12-24 | null | USD | FAIL |
| תנאים כלליים לטיולי אדמה 1 עבור אריאל פל | תנאים כלליים לטיולי אדמה 1 עבור אריאל פל | null 14:00 | null | USD | FAIL |
| תשלום חידוש דרכון.pdf | לאמדינת עבאדי | 2025-02-22 22:10 | null | ARS | FAIL |

**Resumen:** PASS=31 FAIL=93 Total=124

## Notas
- OCR visual aplicado via `pymupdf` (fitz) + `qwen2.5-vl:7b` (Ollama) para PDFs con capa texto <100 chars; para PDFs con texto >=100 se parseo directo
- Geocodificacion via coordenadas conocidas / Nominatim local para direcciones extraidas
- Moneda corregida a EUR para tickets Italia/Europa (ej. B&B Marbo Florence, Capilla Sixtina)