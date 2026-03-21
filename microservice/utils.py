def process_coordinates(lat: float, lon: float) -> tuple[float, float]:
    """
    Recibe latitud y longitud, y las devuelve redondeadas estrictamente a 4 decimales.
    Optimizando la ingesta y coincidencia en la Lógica de Cascada de Nivel 1.
    """
    if lat is None or lon is None:
        raise ValueError("Latitud y longitud no pueden ser nulos.")
        
    return round(float(lat), 4), round(float(lon), 4)

if __name__ == "__main__":
    # Prueba de redondeo conforme al Nivel 1
    lat, lon = -34.603722, -58.381592
    r_lat, r_lon = process_coordinates(lat, lon)
    print(f"Original: {lat}, {lon} -> Procesado: {r_lat}, {r_lon}")
