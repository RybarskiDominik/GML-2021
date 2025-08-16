
kw_dict = {
    '1': '1',
    '2': '2',
    '3': '3',
    '4': '4',
    '5': '5',
    '6': '6',
    '7': '7',
    '8': '8',
    '9': '9',
    'X': '10',
    'A': '11',
    'B': '12',
    'C': '13',
    'D': '14',
    'E': '15',
    'F': '16',
    'G': '17',
    'H': '18',
    'I': '19',
    'J': '20',
    'K': '21',
    'L': '22',
    'M': '23',
    'N': '24',
    'O': '25',
    'P': '26',
    'R': '27',
    'S': '28',
    'T': '29',
    'U': '30',
    'W': '31',
    'Y': '32',
    'Z': '33',
    }

waight = [1, 3, 7, 1, 3, 7, 1, 3, 7, 1, 3, 7]

def kw_generator(kod=None, kw_number=None):
    kw_number = kw_number.zfill(8)
    number = (kod + kw_number)

    value = []
    value = [int(kw_dict.get(i, 0)) for i in number]

    weighted_sum = sum(a * w for a, w in zip(value, waight))/10
    weighted_sum = str(weighted_sum).strip(".")[-1]

    return kod, kw_number, weighted_sum

if __name__ == '__main__':

    key = 'ABCD'
    kw  = '1234'

    kod, numer_kw, weighted_sum = kw_generator(key, kw)
    
    print(f"{kod}/{numer_kw}/{weighted_sum}")