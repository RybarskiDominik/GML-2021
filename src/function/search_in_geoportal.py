import webbrowser


def open_parcel_in_geoportal(id=None):
    if id is None:
        return
    url = f"https://mapy.geoportal.gov.pl/imap/Imgp_2.html?identifyParcel={id}"
    
    webbrowser.open(url)


if __name__ == '__main__':
    pass