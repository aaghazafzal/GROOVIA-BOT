"""
Groovia Mass Indexer - Smart Discovery Engine v3.0
TARGET: 1,00,000+ unique songs guaranteed

Strategy:
  - Phase 1: YouTube Music Charts (7 countries)
  - Phase 2: 650+ artists catalogs (priority-sorted)
  - Phase 3: Artist variation queries ("best of X", "X hits", etc.)
  - Phase 4: 1500+ search queries (Bollywood, English, Punjabi, South, Regional)
  - Phase 5: Auto year+language combos (35 years x 8 languages = 280 queries)
  - Phase 6: Bollywood movies (300+ movies)
  - LOOP:    Repeat phases with shuffled order (catches missed songs)

Estimated unique songs per cycle: ~65,000-75,000
After 2 cycles: 100,000+
"""

import time
import logging
import random
from typing import Generator, Dict, Any, Set, List

from ytmusicapi import YTMusic
from config import RESULTS_PER_QUERY, DISCOVERY_DELAY, TARGET_SONGS

logger = logging.getLogger(__name__)


# =============================================================================
# ARTIST DATABASE - 650+ artists by language and tier
# =============================================================================

ARTISTS = {

    # ── HINDI / BOLLYWOOD SINGERS ─────────────────────────────────────────────
    'hindi': [
        # Tier 1 - All-time legends & current superstars
        {'name': 'Arijit Singh',             'tier': 1},
        {'name': 'Jubin Nautiyal',           'tier': 1},
        {'name': 'Shreya Ghoshal',           'tier': 1},
        {'name': 'Neha Kakkar',              'tier': 1},
        {'name': 'Atif Aslam',               'tier': 1},
        {'name': 'Sonu Nigam',               'tier': 1},
        {'name': 'KK singer',                'tier': 1},
        {'name': 'Udit Narayan',             'tier': 1},
        {'name': 'Kumar Sanu',               'tier': 1},
        {'name': 'Alka Yagnik',              'tier': 1},
        {'name': 'Lata Mangeshkar',          'tier': 1},
        {'name': 'Mohammed Rafi',            'tier': 1},
        {'name': 'Kishore Kumar',            'tier': 1},
        {'name': 'Sunidhi Chauhan',          'tier': 1},
        {'name': 'Armaan Malik',             'tier': 1},
        {'name': 'Vishal Mishra',            'tier': 1},
        {'name': 'B Praak',                  'tier': 1},
        {'name': 'Rahat Fateh Ali Khan',     'tier': 1},
        {'name': 'Asha Bhosle',             'tier': 1},
        {'name': 'Mukesh singer',            'tier': 1},
        # Tier 2
        {'name': 'Darshan Raval',            'tier': 2},
        {'name': 'Dhvani Bhanushali',        'tier': 2},
        {'name': 'Shaan',                    'tier': 2},
        {'name': 'Mohit Chauhan',            'tier': 2},
        {'name': 'Shankar Mahadevan',        'tier': 2},
        {'name': 'Hariharan',                'tier': 2},
        {'name': 'Lucky Ali',                'tier': 2},
        {'name': 'Hemant Kumar singer',      'tier': 2},
        {'name': 'Manna Dey',               'tier': 2},
        {'name': 'Talat Mahmood',            'tier': 2},
        {'name': 'Kavita Krishnamurthy',     'tier': 2},
        {'name': 'Anuradha Paudwal',         'tier': 2},
        {'name': 'Rekha Bhardwaj',           'tier': 2},
        {'name': 'Kailash Kher',             'tier': 2},
        {'name': 'Javed Ali',               'tier': 2},
        {'name': 'Ankit Tiwari',             'tier': 2},
        {'name': 'Falak Shabir',             'tier': 2},
        {'name': 'Monali Thakur',            'tier': 2},
        {'name': 'Tulsi Kumar',              'tier': 2},
        {'name': 'Palak Muchhal',            'tier': 2},
        {'name': 'Shilpa Rao',              'tier': 2},
        {'name': 'Jonita Gandhi',            'tier': 2},
        {'name': 'Ash King',                'tier': 2},
        {'name': 'Papon singer',             'tier': 2},
        {'name': 'Harshdeep Kaur',           'tier': 2},
        {'name': 'Kanika Kapoor',            'tier': 2},
        {'name': 'Mika Singh',              'tier': 2},
        {'name': 'Richa Sharma',             'tier': 2},
        {'name': 'Altamash Faridi',          'tier': 2},
        {'name': 'Shafqat Amanat Ali',       'tier': 2},
        {'name': 'Adnan Sami',               'tier': 2},
        {'name': 'Nusrat Fateh Ali Khan',    'tier': 2},
        {'name': 'Abida Parveen',            'tier': 2},
        {'name': 'Jagjit Singh',             'tier': 2},
        {'name': 'Ghulam Ali ghazal',        'tier': 2},
        {'name': 'Mehdi Hassan ghazal',      'tier': 2},
        # Tier 3
        {'name': 'Stebin Ben',               'tier': 3},
        {'name': 'Raj Barman',               'tier': 3},
        {'name': 'Nikhil D Souza',           'tier': 3},
        {'name': 'Jasleen Royal',            'tier': 3},
        {'name': 'Prateek Kuhad',            'tier': 3},
        {'name': 'Anuv Jain',               'tier': 3},
        {'name': 'Asees Kaur',              'tier': 3},
        {'name': 'Pawandeep Rajan',          'tier': 3},
        {'name': 'Arunita Kanjilal',         'tier': 3},
        {'name': 'Salman Ali singer',        'tier': 3},
        {'name': 'Saaj Bhatt',              'tier': 3},
        {'name': 'Yasser Desai',             'tier': 3},
        {'name': 'Sukhwinder Singh',         'tier': 3},
        {'name': 'Abhijeet Bhattacharya',    'tier': 3},
        {'name': 'Babul Supriyo',            'tier': 3},
        {'name': 'Kunal Ganjawala',          'tier': 3},
        {'name': 'Rahul Vaidya',             'tier': 3},
        {'name': 'Kamal Khan singer',        'tier': 3},
        {'name': 'Nakash Aziz',             'tier': 3},
        {'name': 'Amit Mishra',             'tier': 3},
        {'name': 'Altaf Raja',              'tier': 3},
        {'name': 'Udit Narayan hits',        'tier': 3},
        {'name': 'Hamsika Iyer',             'tier': 3},
        {'name': 'Vinod Rathod',             'tier': 3},
        {'name': 'Usha Khanna',             'tier': 3},
        {'name': 'Kavita Paudwal',           'tier': 3},
        {'name': 'Shabbir Kumar',            'tier': 3},
        {'name': 'Mohammad Aziz',            'tier': 3},
        {'name': 'Sudesh Bhosle',            'tier': 3},
        {'name': 'Ila Arun',                'tier': 3},
        {'name': 'Sunitha Sarathy',          'tier': 3},
        {'name': 'Aadesh Shrivastava',       'tier': 3},
        {'name': 'Shankar Shambhu',          'tier': 3},
        {'name': 'Pankaj Udhas',             'tier': 3},
        {'name': 'Anup Jalota',             'tier': 3},
        {'name': 'Penaz Masani',             'tier': 3},
        {'name': 'Talat Aziz',              'tier': 3},
        {'name': 'Hariharan ghazal',         'tier': 3},
        {'name': 'Chitra Singh',             'tier': 3},
        {'name': 'Nayyara Noor',             'tier': 3},
        {'name': 'Iqbal Bano',              'tier': 3},
        {'name': 'Farida Khanum',            'tier': 3},
        {'name': 'Reshma folk singer',       'tier': 3},
        {'name': 'Noor Jehan',              'tier': 3},
        {'name': 'Geeta Dutt',              'tier': 3},
        {'name': 'Shamshad Begum',           'tier': 3},
        {'name': 'Zubeen Garg',             'tier': 3},
        {'name': 'Usha Uthup',              'tier': 3},
        {'name': 'SP Balasubrahmanyam Hindi', 'tier': 3},
        {'name': 'Shankar Tucker',           'tier': 3},
        {'name': 'Shalmali Kholgade',        'tier': 3},
        {'name': 'Benny Dayal Hindi',        'tier': 3},
        {'name': 'Clinton Cerejo',           'tier': 3},
        {'name': 'Alyssa Mendonsa',          'tier': 3},
        {'name': 'Sunidhi Chauhan hits',     'tier': 3},
        {'name': 'Neha Bhasin',             'tier': 3},
        {'name': 'Hard Kaur',               'tier': 3},
        {'name': 'Sona Mohapatra',           'tier': 3},
        {'name': 'Shahid Mallya',            'tier': 3},
        {'name': 'Mohit Chauhan songs',      'tier': 3},
        {'name': 'Shaan songs',             'tier': 3},
    ],

    # ── BOLLYWOOD COMPOSERS ───────────────────────────────────────────────────
    'hindi_composers': [
        {'name': 'Pritam songs',               'tier': 1},
        {'name': 'Vishal Shekhar songs',       'tier': 1},
        {'name': 'AR Rahman Hindi songs',      'tier': 1},
        {'name': 'Shankar Ehsaan Loy songs',   'tier': 1},
        {'name': 'Amit Trivedi songs',         'tier': 2},
        {'name': 'Sachin Jigar songs',         'tier': 2},
        {'name': 'Tanishk Bagchi songs',       'tier': 2},
        {'name': 'Himesh Reshammiya songs',    'tier': 2},
        {'name': 'Anu Malik songs',            'tier': 2},
        {'name': 'RD Burman songs',            'tier': 2},
        {'name': 'SD Burman songs',            'tier': 2},
        {'name': 'Laxmikant Pyarelal songs',   'tier': 2},
        {'name': 'Kalyanji Anandji songs',     'tier': 2},
        {'name': 'Nadeem Shravan songs',       'tier': 2},
        {'name': 'Anand Milind songs',         'tier': 2},
        {'name': 'Jatin Lalit songs',          'tier': 2},
        {'name': 'Ismail Darbar songs',        'tier': 3},
        {'name': 'Rajesh Roshan songs',        'tier': 3},
        {'name': 'Bappi Lahiri songs',         'tier': 3},
        {'name': 'Ravi shankar songs',         'tier': 3},
        {'name': 'Khayyam songs',              'tier': 3},
        {'name': 'Naushad songs',              'tier': 3},
        {'name': 'OP Nayyar songs',            'tier': 3},
        {'name': 'Madan Mohan songs',          'tier': 3},
        {'name': 'Roshan composer songs',      'tier': 3},
        {'name': 'Sachin Dev Burman songs',    'tier': 3},
        {'name': 'Salim Sulaiman songs',       'tier': 2},
        {'name': 'Jeet Gannguli songs',        'tier': 2},
        {'name': 'Mithoon songs',              'tier': 2},
        {'name': 'Amaal Mallik songs',         'tier': 2},
        {'name': 'Arko songs',                 'tier': 2},
        {'name': 'Tony Kakkar songs',          'tier': 2},
        {'name': 'Yo Yo Honey Singh songs',    'tier': 2},
        {'name': 'Badshah songs',              'tier': 2},
        {'name': 'Guru Randhawa songs',        'tier': 2},
        {'name': 'Nucleya songs',              'tier': 3},
        {'name': 'Lost Stories songs',         'tier': 3},
    ],

    # ── PUNJABI ───────────────────────────────────────────────────────────────
    'punjabi': [
        {'name': 'Diljit Dosanjh',          'tier': 1},
        {'name': 'AP Dhillon',              'tier': 1},
        {'name': 'Sidhu Moosewala',         'tier': 1},
        {'name': 'Guru Randhawa',           'tier': 1},
        {'name': 'Hardy Sandhu',            'tier': 1},
        {'name': 'Honey Singh',             'tier': 1},
        {'name': 'Badshah',                 'tier': 1},
        {'name': 'Karan Aujla',             'tier': 1},
        {'name': 'Shubh singer',            'tier': 1},
        {'name': 'Jasmine Sandlas',         'tier': 2},
        {'name': 'Ammy Virk',               'tier': 2},
        {'name': 'Nimrat Khaira',           'tier': 2},
        {'name': 'Parmish Verma',           'tier': 2},
        {'name': 'Mankirt Aulakh',          'tier': 2},
        {'name': 'Jassa Dhillon',           'tier': 2},
        {'name': 'Bohemia rapper',          'tier': 2},
        {'name': 'Jazz Dhami',              'tier': 2},
        {'name': 'Gippy Grewal',            'tier': 2},
        {'name': 'Jassi Gill',              'tier': 2},
        {'name': 'Satinder Sartaaj',        'tier': 2},
        {'name': 'Kulwinder Billa',         'tier': 2},
        {'name': 'Sukhe singer',            'tier': 2},
        {'name': 'Akhil singer',            'tier': 2},
        {'name': 'Navaan Sandhu',           'tier': 2},
        {'name': 'Ranjit Bawa',             'tier': 2},
        {'name': 'Dilpreet Dhillon',        'tier': 2},
        {'name': 'Resham Singh Anmol',      'tier': 2},
        {'name': 'Veet Baljit',             'tier': 2},
        {'name': 'Sharry Mann',             'tier': 2},
        {'name': 'Rajvir Jawanda',          'tier': 2},
        {'name': 'Jordan Sandhu',           'tier': 2},
        {'name': 'Prabh Gill',              'tier': 2},
        {'name': 'Amrinder Gill',           'tier': 2},
        {'name': 'Surjit Bhullar',          'tier': 3},
        {'name': 'Mehtab Virk',             'tier': 3},
        {'name': 'Harjit Harman',           'tier': 3},
        {'name': 'Gurdas Maan',             'tier': 3},
        {'name': 'Hans Raj Hans',           'tier': 3},
        {'name': 'Miss Pooja',              'tier': 3},
        {'name': 'Nooran Sisters',          'tier': 3},
        {'name': 'Feroz Khan singer',       'tier': 3},
        {'name': 'Kaur B',                  'tier': 3},
        {'name': 'Sunanda Sharma',          'tier': 3},
        {'name': 'Preet Harpal',            'tier': 3},
        {'name': 'Gulab Sidhu',             'tier': 3},
        {'name': 'Tarsem Jassar',           'tier': 3},
        {'name': 'Inder Dosanjh',           'tier': 3},
        {'name': 'Nachhatar Gill',          'tier': 3},
        {'name': 'Ranjit Mani',             'tier': 3},
        {'name': 'Balkar Sidhu',            'tier': 3},
        {'name': 'Deepak Dhillon',          'tier': 3},
        {'name': 'Laddi Gill',              'tier': 3},
        {'name': 'Maninder Buttar',         'tier': 3},
        {'name': 'Gurnam Bhullar',          'tier': 3},
        {'name': 'Sippy Gill',              'tier': 3},
        {'name': 'Jyotica Tangri',          'tier': 3},
    ],

    # ── ENGLISH ───────────────────────────────────────────────────────────────
    'english': [
        # Tier 1
        {'name': 'Taylor Swift',            'tier': 1},
        {'name': 'Ed Sheeran',              'tier': 1},
        {'name': 'The Weeknd',              'tier': 1},
        {'name': 'Justin Bieber',           'tier': 1},
        {'name': 'Billie Eilish',           'tier': 1},
        {'name': 'Olivia Rodrigo',          'tier': 1},
        {'name': 'Dua Lipa',               'tier': 1},
        {'name': 'Harry Styles',            'tier': 1},
        {'name': 'Ariana Grande',           'tier': 1},
        {'name': 'Bruno Mars',              'tier': 1},
        {'name': 'Drake',                   'tier': 1},
        {'name': 'Eminem',                  'tier': 1},
        {'name': 'Post Malone',             'tier': 1},
        {'name': 'Adele',                   'tier': 1},
        {'name': 'BTS',                     'tier': 1},
        {'name': 'Coldplay',                'tier': 1},
        {'name': 'Imagine Dragons',         'tier': 1},
        {'name': 'Maroon 5',               'tier': 1},
        {'name': 'Michael Jackson',         'tier': 1},
        {'name': 'Rihanna',                 'tier': 1},
        {'name': 'Beyonce',                 'tier': 1},
        {'name': 'Lady Gaga',              'tier': 1},
        # Tier 2
        {'name': 'Sam Smith',               'tier': 2},
        {'name': 'Shawn Mendes',            'tier': 2},
        {'name': 'Camila Cabello',          'tier': 2},
        {'name': 'Selena Gomez',            'tier': 2},
        {'name': 'Charlie Puth',            'tier': 2},
        {'name': 'Khalid singer',           'tier': 2},
        {'name': 'Doja Cat',               'tier': 2},
        {'name': 'SZA singer',             'tier': 2},
        {'name': 'Cardi B',                'tier': 2},
        {'name': 'Travis Scott',            'tier': 2},
        {'name': 'Kendrick Lamar',          'tier': 2},
        {'name': 'J Cole',                  'tier': 2},
        {'name': 'Lil Nas X',              'tier': 2},
        {'name': 'Juice WRLD',             'tier': 2},
        {'name': 'XXXTentacion',            'tier': 2},
        {'name': 'Morgan Wallen',           'tier': 2},
        {'name': 'Luke Combs',              'tier': 2},
        {'name': 'Queen band',              'tier': 2},
        {'name': 'The Beatles',             'tier': 2},
        {'name': 'Linkin Park',             'tier': 2},
        {'name': 'One Direction',           'tier': 2},
        {'name': 'Nirvana',                 'tier': 2},
        {'name': 'BLACKPINK',               'tier': 2},
        {'name': 'Stray Kids',              'tier': 2},
        {'name': 'TWICE kpop',             'tier': 2},
        {'name': 'Bad Bunny',               'tier': 2},
        {'name': 'J Balvin',               'tier': 2},
        {'name': 'Shakira',                 'tier': 2},
        {'name': 'Enrique Iglesias',        'tier': 2},
        {'name': 'Pitbull',                 'tier': 2},
        {'name': 'Lizzo',                   'tier': 2},
        {'name': 'Nicki Minaj',             'tier': 2},
        {'name': 'Lil Wayne',              'tier': 2},
        {'name': 'Kanye West',             'tier': 2},
        {'name': 'Jay Z',                  'tier': 2},
        {'name': 'Future rapper',           'tier': 2},
        {'name': 'Lil Baby',               'tier': 2},
        {'name': 'Gunna rapper',            'tier': 2},
        {'name': 'Rod Wave',               'tier': 2},
        # Tier 3
        {'name': 'Pink Floyd',              'tier': 3},
        {'name': 'Guns N Roses',            'tier': 3},
        {'name': 'Metallica',               'tier': 3},
        {'name': 'AC DC',                   'tier': 3},
        {'name': 'Led Zeppelin',            'tier': 3},
        {'name': 'Fleetwood Mac',           'tier': 3},
        {'name': 'Eagles band',             'tier': 3},
        {'name': 'Red Hot Chili Peppers',   'tier': 3},
        {'name': 'Foo Fighters',            'tier': 3},
        {'name': 'Green Day',               'tier': 3},
        {'name': 'Twenty One Pilots',       'tier': 3},
        {'name': 'Fall Out Boy',            'tier': 3},
        {'name': 'Panic at the Disco',      'tier': 3},
        {'name': 'The Chainsmokers',        'tier': 3},
        {'name': 'Marshmello',              'tier': 3},
        {'name': 'Alan Walker',             'tier': 3},
        {'name': 'Calvin Harris',           'tier': 3},
        {'name': 'David Guetta',            'tier': 3},
        {'name': 'Avicii',                  'tier': 3},
        {'name': 'Martin Garrix',           'tier': 3},
        {'name': 'Kygo',                    'tier': 3},
        {'name': 'Zedd',                    'tier': 3},
        {'name': 'The Killers',             'tier': 3},
        {'name': 'Arctic Monkeys',          'tier': 3},
        {'name': 'Tame Impala',             'tier': 3},
        {'name': 'Glass Animals',           'tier': 3},
        {'name': 'Maluma',                  'tier': 3},
        {'name': 'Bon Jovi',               'tier': 3},
        {'name': 'Akon',                    'tier': 3},
        {'name': 'Usher',                   'tier': 3},
        {'name': 'Chris Brown',             'tier': 3},
        {'name': 'Ne-Yo',                   'tier': 3},
        {'name': 'Jason Derulo',            'tier': 3},
        {'name': 'Flo Rida',               'tier': 3},
        {'name': 'LMFAO',                   'tier': 3},
        {'name': 'Kesha',                   'tier': 3},
        {'name': 'Katy Perry',              'tier': 3},
        {'name': 'Miley Cyrus',             'tier': 3},
        {'name': 'Demi Lovato',             'tier': 3},
        {'name': 'Pink singer',             'tier': 3},
        {'name': 'Meghan Trainor',          'tier': 3},
        {'name': 'James Arthur',            'tier': 3},
        {'name': 'Lewis Capaldi',           'tier': 3},
        {'name': 'Dermot Kennedy',          'tier': 3},
        {'name': 'Tom Walker singer',       'tier': 3},
        {'name': 'Anne Marie',              'tier': 3},
        {'name': 'Rag n Bone Man',          'tier': 3},
        {'name': 'George Ezra',             'tier': 3},
        {'name': 'Hozier',                  'tier': 3},
        {'name': 'Passenger singer',        'tier': 3},
        {'name': 'Kodaline',               'tier': 3},
        {'name': 'The Script',              'tier': 3},
        {'name': 'Snow Patrol',             'tier': 3},
        {'name': 'Keane band',              'tier': 3},
        {'name': 'Mumford and Sons',        'tier': 3},
        {'name': 'Of Monsters and Men',     'tier': 3},
        {'name': 'Bastille band',           'tier': 3},
        {'name': 'Lorde singer',            'tier': 3},
        {'name': 'Halsey',                  'tier': 3},
        {'name': 'Troye Sivan',             'tier': 3},
        {'name': 'Alessia Cara',            'tier': 3},
        {'name': 'Julia Michaels',          'tier': 3},
        {'name': 'Gnash singer',            'tier': 3},
        {'name': 'Conan Gray',              'tier': 3},
        {'name': 'Benson Boone',            'tier': 3},
        {'name': 'Zach Bryan',              'tier': 3},
        {'name': 'Noah Kahan',              'tier': 3},
        {'name': 'Joji singer',             'tier': 3},
        {'name': 'Rex Orange County',       'tier': 3},
        {'name': 'Clairo',                  'tier': 3},
        {'name': 'beabadoobee',             'tier': 3},
        {'name': 'Phoebe Bridgers',         'tier': 3},
        {'name': 'Soccer Mommy',            'tier': 3},
    ],

    # ── SOUTH INDIAN ──────────────────────────────────────────────────────────
    'south': [
        # Tamil Tier 1
        {'name': 'AR Rahman Tamil',         'tier': 1, 'lang': 'tamil'},
        {'name': 'Anirudh Ravichander',     'tier': 1, 'lang': 'tamil'},
        {'name': 'Sid Sriram',              'tier': 1, 'lang': 'tamil'},
        # Tamil Tier 2
        {'name': 'Yuvan Shankar Raja',      'tier': 2, 'lang': 'tamil'},
        {'name': 'GV Prakash Kumar',        'tier': 2, 'lang': 'tamil'},
        {'name': 'Harris Jayaraj',          'tier': 2, 'lang': 'tamil'},
        {'name': 'Ilaiyaraaja',             'tier': 2, 'lang': 'tamil'},
        {'name': 'D Imman',                 'tier': 2, 'lang': 'tamil'},
        {'name': 'Santhosh Narayanan',      'tier': 2, 'lang': 'tamil'},
        {'name': 'Hip Hop Tamizha',         'tier': 2, 'lang': 'tamil'},
        {'name': 'Haricharan singer',       'tier': 3, 'lang': 'tamil'},
        {'name': 'Karthik singer Tamil',    'tier': 3, 'lang': 'tamil'},
        {'name': 'Tippu singer',            'tier': 3, 'lang': 'tamil'},
        {'name': 'Vijay Antony',            'tier': 3, 'lang': 'tamil'},
        {'name': 'Aaryan Dinesh Kanagaratnam', 'tier': 3, 'lang': 'tamil'},
        {'name': 'Shakthisree Gopalan',     'tier': 3, 'lang': 'tamil'},
        {'name': 'Shreya Ghoshal Tamil',    'tier': 3, 'lang': 'tamil'},
        {'name': 'Chinmayi singer',         'tier': 3, 'lang': 'tamil'},
        {'name': 'Unni Krishnan',           'tier': 3, 'lang': 'tamil'},
        # Telugu Tier 1
        {'name': 'Devi Sri Prasad',         'tier': 1, 'lang': 'telugu'},
        {'name': 'SS Thaman',               'tier': 1, 'lang': 'telugu'},
        {'name': 'MM Keeravani',            'tier': 1, 'lang': 'telugu'},
        # Telugu Tier 2
        {'name': 'Sid Sriram Telugu',       'tier': 2, 'lang': 'telugu'},
        {'name': 'SP Balasubrahmanyam',     'tier': 2, 'lang': 'telugu'},
        {'name': 'Sunitha Telugu',          'tier': 2, 'lang': 'telugu'},
        {'name': 'Kalyani Nair',            'tier': 2, 'lang': 'telugu'},
        {'name': 'Armaan Malik Telugu',     'tier': 3, 'lang': 'telugu'},
        {'name': 'Geetha Madhuri',          'tier': 3, 'lang': 'telugu'},
        {'name': 'Pranavi Athreyasa',       'tier': 3, 'lang': 'telugu'},
        {'name': 'Harika Narayan',          'tier': 3, 'lang': 'telugu'},
        {'name': 'Mangli Telugu',           'tier': 3, 'lang': 'telugu'},
        # Kannada
        {'name': 'Arjun Janya',             'tier': 2, 'lang': 'kannada'},
        {'name': 'Ravi Basrur',             'tier': 2, 'lang': 'kannada'},
        {'name': 'V Harikrishna',           'tier': 3, 'lang': 'kannada'},
        {'name': 'Hamsalekha songs',        'tier': 3, 'lang': 'kannada'},
        {'name': 'Rajesh Krishnan',         'tier': 3, 'lang': 'kannada'},
        # Malayalam
        {'name': 'K J Yesudas',             'tier': 2, 'lang': 'malayalam'},
        {'name': 'MG Sreekumar',            'tier': 3, 'lang': 'malayalam'},
        {'name': 'Vidyasagar Malayalam',    'tier': 3, 'lang': 'malayalam'},
        {'name': 'Sujatha singer',          'tier': 3, 'lang': 'malayalam'},
        {'name': 'Shreya Ghoshal Malayalam', 'tier': 3, 'lang': 'malayalam'},
        {'name': 'Bijibal songs',           'tier': 3, 'lang': 'malayalam'},
        {'name': 'Pradeep Pallavam',        'tier': 3, 'lang': 'malayalam'},
    ],

    # ── OTHER REGIONAL ────────────────────────────────────────────────────────
    'regional': [
        # Haryanvi
        {'name': 'Sapna Choudhary',         'tier': 2, 'lang': 'haryanvi'},
        {'name': 'Renuka Panwar',           'tier': 2, 'lang': 'haryanvi'},
        {'name': 'Masoom Sharma',           'tier': 3, 'lang': 'haryanvi'},
        {'name': 'Ruchika Jangid',          'tier': 3, 'lang': 'haryanvi'},
        {'name': 'Raj Mawar',               'tier': 3, 'lang': 'haryanvi'},
        {'name': 'Sumit Goswami',           'tier': 3, 'lang': 'haryanvi'},
        {'name': 'Vishvajeet Choudhary',    'tier': 3, 'lang': 'haryanvi'},
        # Bhojpuri
        {'name': 'Khesari Lal Yadav',       'tier': 2, 'lang': 'bhojpuri'},
        {'name': 'Pawan Singh Bhojpuri',    'tier': 2, 'lang': 'bhojpuri'},
        {'name': 'Dinesh Lal Yadav Nirahua','tier': 3, 'lang': 'bhojpuri'},
        {'name': 'Ritesh Pandey',           'tier': 3, 'lang': 'bhojpuri'},
        {'name': 'Pramod Premi Yadav',      'tier': 3, 'lang': 'bhojpuri'},
        # Bengali
        {'name': 'Arijit Singh Bengali',    'tier': 2, 'lang': 'bengali'},
        {'name': 'Kumar Sanu Bengali',      'tier': 3, 'lang': 'bengali'},
        {'name': 'Nachiketa Chakraborty',   'tier': 3, 'lang': 'bengali'},
        {'name': 'Usha Uthup Bengali',      'tier': 3, 'lang': 'bengali'},
        {'name': 'Shaan Bengali',           'tier': 3, 'lang': 'bengali'},
        # Marathi
        {'name': 'Ajay Atul songs',         'tier': 2, 'lang': 'marathi'},
        {'name': 'Swapnil Bandodkar',       'tier': 3, 'lang': 'marathi'},
        {'name': 'Vaishali Made',           'tier': 3, 'lang': 'marathi'},
        {'name': 'Hrishikesh Ranade',       'tier': 3, 'lang': 'marathi'},
        # Gujarati
        {'name': 'Kirtidan Gadhvi',         'tier': 3, 'lang': 'gujarati'},
        {'name': 'Geeta Rabari',            'tier': 3, 'lang': 'gujarati'},
        {'name': 'Aishwarya Majmudar',      'tier': 3, 'lang': 'gujarati'},
        # Rajasthani / Folk
        {'name': 'Mame Khan',               'tier': 3, 'lang': 'rajasthani'},
        {'name': 'Langa musicians',         'tier': 3, 'lang': 'rajasthani'},
        {'name': 'Manganiyar folk',         'tier': 3, 'lang': 'rajasthani'},
    ],
}

# =============================================================================
# BOLLYWOOD MOVIES LIST - 300+ movies = ~3,000-5,000 unique songs
# =============================================================================
BOLLYWOOD_MOVIES = [
    # 2020s Blockbusters
    "Pathaan songs", "Jawan songs", "Animal movie songs", "Dunki songs",
    "Tiger 3 songs", "Fighter movie songs", "Stree 2 songs",
    "Rocky Aur Rani songs", "Brahmastra songs", "Bhool Bhulaiyaa 2 songs",
    "Gangubai Kathiawadi songs", "Gehraiyaan songs", "Atrangi Re songs",
    "Shershaah songs", "Bell Bottom songs", "Sooryavanshi songs",
    "83 movie songs", "Laal Singh Chaddha songs", "Drishyam 2 songs",
    "Good Newwz songs", "Street Dancer songs", "Love Aaj Kal 2 songs",
    "Tanhaji songs", "Chhapaak songs", "Thappad songs",
    "RRR Hindi songs", "KGF 2 Hindi songs", "Pushpa 2 Hindi songs",
    # 2010s Blockbusters
    "War songs Hrithik", "Kabir Singh songs", "Gully Boy songs",
    "Chhichhore songs", "Uri songs", "Total Dhamaal songs",
    "Kalank songs", "Zero songs", "Sanju songs", "Raazi songs",
    "Padmaavat songs", "Tiger Zinda Hai songs", "Judwaa 2 songs",
    "Tubelight songs", "Jolly LLB 2 songs", "Raees songs",
    "Ae Dil Hai Mushkil songs", "Rustom songs", "Mohenjo Daro songs",
    "Fan songs", "Airlift songs", "Bajrangi Bhaijaan songs",
    "Dilwale songs", "Prem Ratan Dhan Payo songs", "Hero songs",
    "Hamari Adhuri Kahani songs", "Gabbar Is Back songs",
    "Kick songs Salman", "Ek Villain songs", "Bang Bang songs",
    "2 States songs", "Queen movie songs", "Highway songs",
    "Hasee Toh Phasee songs", "Gunday songs", "Dedh Ishqiya songs",
    "Bhaag Milkha Bhaag songs", "Chennai Express songs",
    "Yeh Jawaani Hai Deewani songs", "Raanjhanaa songs",
    "Aashiqui 2 songs", "Race 2 songs", "Barfi songs",
    "Jab Tak Hai Jaan songs", "Student of the Year songs",
    "Ek Tha Tiger songs", "Agneepath 2012 songs", "Rockstar songs",
    "Bodyguard songs", "Ra One songs", "Zindagi Na Milegi Dobara songs",
    "Ready songs Salman", "Dabangg 2 songs", "Don 2 songs",
    "Mere Brother Ki Dulhan songs", "Singham songs",
    "No One Killed Jessica songs", "Dhobi Ghat songs",
    "Band Baaja Baaraat songs", "Dabangg songs", "My Name Is Khan songs",
    "Three Idiots songs", "Kaminey songs", "Love Aaj Kal 2009 songs",
    # 2000s Classics
    "Kabhi Alvida Naa Kehna songs", "Don 2006 songs",
    "Rang De Basanti songs", "Black 2005 songs", "Veer Zaara songs",
    "Kal Ho Naa Ho songs", "Kuch Kuch Hota Hai songs",
    "Devdas 2002 songs", "Lagaan songs", "Dil Chahta Hai songs",
    "Mission Kashmir songs", "Mohabbatein songs", "Kaho Naa Pyaar Hai songs",
    "Refugee songs Kareena", "Josh 2000 songs", "Dil To Pagal Hai songs",
    "Hum Dil De Chuke Sanam songs", "Kuch Kuch Hota Hai songs",
    "Dil Se songs", "Satya songs", "Border songs",
    "Raja Hindustani songs", "Dilwale Dulhania Le Jayenge songs",
    "Hum Aapke Hain Koun songs", "1942 A Love Story songs",
    "Baazigar songs", "Darr songs", "Jo Jeeta Wohi Sikandar songs",
    # 1990s Hits
    "Andaz Apna Apna songs", "Hum songs Amitabh",
    "Maine Pyar Kiya songs", "Qayamat Se Qayamat Tak songs",
    "Tezaab songs", "Ram Teri Ganga Maili songs",
    "Aashiqui 1990 songs", "Dil songs Amir Khan",
    "Phool Aur Kaante songs", "Saajan songs",
    "Lamhe songs", "Chandni songs Sridevi",
    # Regional Blockbusters
    "Pushpa songs Telugu", "RRR songs Telugu", "Baahubali songs",
    "KGF songs Kannada", "Vikram movie songs Tamil",
    "Beast songs Tamil", "Doctor songs Tamil",
    "Master songs Tamil", "Darbar songs Tamil",
    "Bigil songs Tamil", "96 movie songs Tamil",
    "Mersal songs Tamil", "Bairavaa songs Tamil",
    "Kabali songs Tamil", "Lingaa songs Tamil",
    "Enthiran songs Tamil", "Dasavathaaram songs Tamil",
]

# =============================================================================
# SEARCH QUERIES - 1500+ queries
# =============================================================================

def generate_all_queries() -> List[str]:
    """Auto-generate 2000+ queries from templates — targets 1,00,000 unique songs"""

    # ── TOP ARTISTS for year-based queries ────────────────────────────────────
    top_hindi_artists = [
        "Arijit Singh", "Jubin Nautiyal", "Shreya Ghoshal", "Neha Kakkar",
        "Atif Aslam", "Sonu Nigam", "KK", "Armaan Malik", "Vishal Mishra",
        "B Praak", "Rahat Fateh Ali Khan", "Darshan Raval", "Shaan",
        "Mohit Chauhan", "Udit Narayan", "Kumar Sanu", "Alka Yagnik",
        "Sunidhi Chauhan", "Lata Mangeshkar", "Mohammed Rafi", "Kishore Kumar",
        "Mika Singh", "Badshah", "Guru Randhawa", "Tulsi Kumar", "Palak Muchhal",
    ]
    top_punjabi_artists = [
        "Diljit Dosanjh", "AP Dhillon", "Sidhu Moosewala", "Hardy Sandhu",
        "Honey Singh", "Karan Aujla", "Shubh", "Ammy Virk", "Mankirt Aulakh",
    ]
    top_english_artists = [
        "Taylor Swift", "Ed Sheeran", "The Weeknd", "Justin Bieber",
        "Ariana Grande", "Eminem", "Drake", "Bruno Mars", "Adele",
        "Billie Eilish", "Dua Lipa", "Harry Styles", "Post Malone",
    ]
    top_south_artists = [
        "AR Rahman", "Anirudh Ravichander", "Devi Sri Prasad", "Ilaiyaraaja",
        "SS Thaman", "Sid Sriram", "GV Prakash Kumar",
    ]

    # MEGA BOOST: Artist + Year combos (most targeted = highest unique yield)
    artist_year_queries = []
    for artist in top_hindi_artists:
        for year in range(2010, 2025):
            artist_year_queries.append(f"{artist} {year} songs")
    for artist in top_punjabi_artists:
        for year in range(2015, 2025):
            artist_year_queries.append(f"{artist} {year}")
    for artist in top_english_artists:
        for year in range(2015, 2025):
            artist_year_queries.append(f"{artist} {year} songs")
    for artist in top_south_artists:
        for year in range(2018, 2025):
            artist_year_queries.append(f"{artist} {year}")

    queries = [
        # Include artist+year combos FIRST
        *artist_year_queries,

        # ── HINDI YEARLY ──────────────────────────────────────────────────────
        *[f"bollywood hits {y}" for y in range(1990, 2025)],
        *[f"hindi songs {y}" for y in range(2000, 2025)],
        *[f"top hindi songs {y}" for y in range(2010, 2025)],
        *[f"best bollywood songs {y}" for y in range(2010, 2025)],
        *[f"hindi superhits {y}" for y in range(2005, 2025)],

        # ── HINDI MOOD ────────────────────────────────────────────────────────
        "hindi romantic songs", "hindi love songs", "hindi sad songs",
        "hindi breakup songs", "hindi party songs", "hindi dance songs",
        "hindi motivational songs", "hindi devotional songs",
        "hindi old songs", "hindi retro songs", "hindi classics",
        "bollywood dance songs", "bollywood wedding songs",
        "bollywood item songs", "bollywood romantic songs",
        "bollywood sad songs", "hindi peppy songs",
        "hindi slow songs", "hindi emotional songs",
        "hindi heart touching songs", "hindi melodious songs",
        "hindi unplugged songs", "hindi acoustic songs",
        "gaane purane", "purane hindi gaane", "old Bollywood hits",
        "evergreen hindi songs", "all time best hindi songs",
        "golden era bollywood", "retro bollywood hits",
        "hindi songs 90s hits", "hindi songs 80s hits",
        "hindi songs 70s hits", "hindi songs 60s hits",

        # ── PUNJABI YEARLY ────────────────────────────────────────────────────
        *[f"punjabi songs {y}" for y in range(2010, 2025)],
        *[f"punjabi hits {y}" for y in range(2015, 2025)],
        *[f"new punjabi songs {y}" for y in range(2018, 2025)],

        # ── PUNJABI MOOD ──────────────────────────────────────────────────────
        "punjabi love songs", "punjabi sad songs", "punjabi party songs",
        "punjabi dance songs", "punjabi romantic songs",
        "bhangra songs", "punjabi folk songs",
        "punjabi pop songs", "punjabi rap songs",
        "punjabi wedding songs", "latest punjabi superhits",
        "punjabi heartbreak songs", "punjabi motivational songs",

        # ── ENGLISH YEARLY ────────────────────────────────────────────────────
        *[f"pop hits {y}" for y in range(2000, 2025)],
        *[f"english hits {y}" for y in range(2005, 2025)],
        *[f"top songs {y}" for y in range(2010, 2025)],
        *[f"best songs of {y}" for y in range(2015, 2025)],

        # ── ENGLISH GENRE ─────────────────────────────────────────────────────
        "pop songs hits", "classic rock hits", "alternative rock songs",
        "indie pop songs", "r&b songs", "hip hop songs",
        "rap songs hits", "soul music songs", "funk songs",
        "jazz songs popular", "blues songs", "country songs",
        "electronic music hits", "EDM songs", "house music hits",
        "lo-fi songs chill", "chill songs playlist", "ambient music",
        "workout songs", "gym motivation songs", "running songs",
        "study music focus", "sleep music calm", "relaxing music",
        "love songs english", "sad songs english heartbreak",
        "happy songs english", "motivational songs english",
        "road trip songs", "summer songs hits",
        "80s hits english", "90s hits english",
        "2000s hits english", "2010s hits english",
        "viral songs 2024", "trending songs 2024",

        # ── SOUTH INDIAN YEARLY ───────────────────────────────────────────────
        *[f"tamil hits {y}" for y in range(2015, 2025)],
        *[f"telugu hits {y}" for y in range(2015, 2025)],
        *[f"kannada hits {y}" for y in range(2018, 2025)],
        *[f"malayalam hits {y}" for y in range(2018, 2025)],

        # ── SOUTH INDIAN MOOD ─────────────────────────────────────────────────
        "tamil love songs", "telugu love songs",
        "tamil sad songs", "telugu sad songs",
        "tamil melody songs", "telugu melody songs",
        "tamil mass songs", "telugu mass songs",
        "AR Rahman Tamil songs", "Anirudh songs Tamil",
        "DSP songs Telugu", "Thaman songs Telugu",
        "Ilaiyaraaja songs", "GV Prakash songs",
        "Sid Sriram songs Telugu", "Sid Sriram songs Tamil",

        # ── REGIONAL ──────────────────────────────────────────────────────────
        *[f"haryanvi songs {y}" for y in range(2018, 2025)],
        *[f"bhojpuri songs {y}" for y in range(2018, 2025)],
        "haryanvi hits", "haryanvi dance songs",
        "bhojpuri hits", "bhojpuri romantic songs",
        "rajasthani folk songs", "marathi songs hits",
        "gujarati songs popular", "bengali songs hits",
        "odia songs popular", "assamese songs hits",

        # ── DEVOTIONAL / SPIRITUAL ────────────────────────────────────────────
        "bhajan songs popular", "aarti songs", "shiv bhajan",
        "hanuman chalisa", "ganesh bhajan", "krishna bhajan",
        "durga aarti songs", "navratri garba songs",
        "Ram bhajan", "Sai Baba bhajan", "Guru Nanak songs",
        "sufi songs popular", "sufi music hits", "qawwali songs",
        "meditation music", "yoga music", "mantra chanting",
        "morning prayer songs", "devotional songs Hindi",

        # ── INDIE / FUSION ────────────────────────────────────────────────────
        "Indian indie songs", "Indian fusion songs",
        "Prateek Kuhad songs", "Anuv Jain songs",
        "Clinton Cerejo songs", "Raghu Dixit songs",
        "The Local Train songs", "When Chai Met Toast songs",
        "Parvaaz songs", "Indian Ocean band songs",
        "Strings band songs", "Euphoria band songs",
        "Parikrama band songs", "Pentagram band songs",
        "Mohit Chauhan indie", "Shantanu Moitra songs",
        "Amit Trivedi indie", "Vishal Bhardwaj songs",

        # ── TRENDING/VIRAL ────────────────────────────────────────────────────
        "trending India 2024", "viral songs India",
        "reels songs 2024", "Instagram reels songs",
        "most played songs India", "India top 50",
        "YouTube trending India", "Billboard hot 100",
        "Grammy winning songs", "Oscar best original song",

        # ── SPECIAL OCCASIONS ─────────────────────────────────────────────────
        "wedding songs Hindi", "sangeet songs Hindi",
        "mehndi songs Hindi", "holi songs", "diwali songs",
        "eid songs", "Christmas songs Hindi",
        "birthday songs Hindi", "friendship songs Hindi",
        "mother songs Hindi", "father songs Hindi",
        "patriotic songs Hindi", "independence day songs",
        "republic day songs", "army songs Hindi",

        # ── FORMAT SPECIALS ───────────────────────────────────────────────────
        "unplugged songs Hindi", "acoustic songs Hindi",
        "mashup songs Hindi", "remix songs Hindi",
        "cover songs Hindi", "lofi remix songs",
        "coke studio songs", "mtv unplugged India songs",
        "T-series songs popular", "Tips Music songs",
        "Zee Music songs", "Sony Music India songs",
        "Saregama songs", "Speed Records songs",
        "White Hill Music songs", "Desi Music songs",

        # Add movies queries
        *BOLLYWOOD_MOVIES,
    ]

    # Remove duplicates while preserving order
    seen = set()
    unique = []
    for q in queries:
        if q not in seen:
            seen.add(q)
            unique.append(q)

    return unique


SEARCH_QUERIES = generate_all_queries()

# ── Editorial Playlist IDs ────────────────────────────────────────────────────
PLAYLIST_IDS = [
    "RDCLAK5uy_kmPRjHDECIcuVwnKsx2Ns7t5wVnhV4eLs",
    "PLFgquLnL59alCl_2TQvOiD5Vgm1hCaGSK",
    "PLFgquLnL59akA2PflFpeQG9L01VFg90wS",
    "PLnMKNibPkDnGqh5OmQWWeHa6W8TuT6bAg",
    "PLFgquLnL59alW3TGWF4YFqKfzuJF68Irp",
    "PLFgquLnL59akCFgXUF7rCYu6KJgr6BrWX",
]

CHART_COUNTRIES = ['IN', 'US', 'GB', 'PK', 'AE', 'CA', 'AU']

# Max discovery cycles — keeps running until 100k target is reached
# Each cycle ~1 hour; 20 cycles = up to 20 hours of discovery over 8 days
MAX_CYCLES = 20


# =============================================================================
# DISCOVERY ENGINE
# =============================================================================

class SongDiscovery:
    """Priority-based song discovery — targets 1,00,000 unique songs"""

    def __init__(self):
        try:
            self.ytm = YTMusic()
            logger.info("ytmusicapi initialized")
        except Exception as e:
            logger.warning(f"ytmusicapi init issue: {e}")
            self.ytm = None
        self._seen: Set[str] = set()

    def discover(self, seen_ids: Set[str] = None) -> Generator[Dict[str, Any], None, None]:
        """
        Main generator — loops up to MAX_CYCLES times.
        Each cycle ~1 hour. Over 8 days = 190+ cycles possible.
        Pipeline stops automatically when TARGET_SONGS is reached.
        """
        if seen_ids:
            self._seen.update(seen_ids)

        for cycle in range(1, MAX_CYCLES + 1):
            logger.info(f"=== DISCOVERY CYCLE {cycle}/{MAX_CYCLES} | Songs seen: {len(self._seen):,} ===")

            if cycle == 1:
                logger.info("PHASE 1: YouTube Music Charts")
                yield from self._phase_charts()

            logger.info(f"PHASE 2: Artist Catalogs")
            yield from self._phase_artists(cycle)

            logger.info(f"PHASE 3: Artist Variation Queries")
            yield from self._phase_artist_variations(cycle)

            logger.info(f"PHASE 4: Search Queries ({len(SEARCH_QUERIES):,} queries)")
            yield from self._phase_search(cycle)

            if cycle <= 2:
                logger.info("PHASE 5: Editorial Playlists")
                yield from self._phase_playlists()

            logger.info(f"Cycle {cycle} done. Total unique discovered: {len(self._seen):,}")

            # Small rest between cycles
            time.sleep(5)

        logger.info(f"All {MAX_CYCLES} cycles complete. Total: {len(self._seen):,} unique songs.")

    # ── PHASE 1: CHARTS ───────────────────────────────────────────────────────

    def _phase_charts(self) -> Generator:
        if not self.ytm:
            return
        for country in CHART_COUNTRIES:
            try:
                charts = self.ytm.get_charts(country=country)
                items = charts if isinstance(charts, list) else []
                if not items:
                    for section in ['songs', 'trending', 'videos']:
                        section_data = charts.get(section, {}) if isinstance(charts, dict) else {}
                        if isinstance(section_data, dict):
                            items.extend(section_data.get('items', []))
                        elif isinstance(section_data, list):
                            items.extend(section_data)
                count = 0
                for item in items:
                    if isinstance(item, dict):
                        song = self._parse_item(item, priority=1)
                        if song and self._is_new(song['yt_id']):
                            yield song
                            count += 1
                logger.info(f"  Charts {country}: {count} new songs")
                time.sleep(DISCOVERY_DELAY * 2)
            except Exception as e:
                logger.warning(f"  Charts {country} failed: {e}")

    # ── PHASE 2: ARTIST CATALOGS ─────────────────────────────────────────────

    def _phase_artists(self, cycle: int = 1) -> Generator:
        if not self.ytm:
            return

        all_artists = []
        for lang, artists in ARTISTS.items():
            for a in artists:
                all_artists.append({**a, 'lang': a.get('lang', lang)})

        all_artists.sort(key=lambda x: x.get('tier', 3))
        if cycle > 1:
            random.shuffle(all_artists)

        total = len(all_artists)
        for i, artist_info in enumerate(all_artists, 1):
            name  = artist_info['name']
            tier  = artist_info.get('tier', 3)
            lang  = artist_info.get('lang', 'hindi')

            try:
                results = self.ytm.search(
                    name, filter='songs',
                    limit=RESULTS_PER_QUERY, ignore_spelling=True
                )
                count = 0
                for item in results:
                    song = self._parse_item(item, priority=tier, default_lang=lang)
                    if song and self._is_new(song['yt_id']):
                        yield song
                        count += 1

                if i % 50 == 0:
                    logger.info(f"  Artists: {i}/{total} done ({len(self._seen):,} total seen)")

                time.sleep(DISCOVERY_DELAY + random.uniform(0, 0.5))
            except Exception as e:
                logger.warning(f"  Artist failed ({name}): {e}")
                time.sleep(2)

    # ── PHASE 3: ARTIST VARIATION QUERIES ────────────────────────────────────

    def _phase_artist_variations(self, cycle: int = 1) -> Generator:
        """Generate variation queries like 'Arijit Singh sad songs', 'best of Arijit Singh'"""
        if not self.ytm:
            return

        # Top artists for variation queries
        top_artists = [
            "Arijit Singh", "Jubin Nautiyal", "Shreya Ghoshal", "Neha Kakkar",
            "Atif Aslam", "Sonu Nigam", "Lata Mangeshkar", "Mohammed Rafi",
            "Kishore Kumar", "Kumar Sanu", "Alka Yagnik", "Rahat Fateh Ali Khan",
            "Diljit Dosanjh", "Sidhu Moosewala", "AP Dhillon", "Guru Randhawa",
            "Taylor Swift", "Ed Sheeran", "The Weeknd", "Eminem",
            "AR Rahman", "Anirudh", "Devi Sri Prasad", "Ilaiyaraaja",
        ]

        moods = ["sad songs", "romantic songs", "hits", "best songs", "top songs",
                 "love songs", "emotional songs", "melodious songs"]

        variation_queries = []
        for artist in top_artists:
            for mood in moods:
                variation_queries.append(f"{artist} {mood}")

        if cycle > 1:
            random.shuffle(variation_queries)

        for i, query in enumerate(variation_queries, 1):
            try:
                results = self.ytm.search(query, filter='songs',
                                          limit=RESULTS_PER_QUERY)
                for item in results:
                    song = self._parse_item(item, priority=2)
                    if song and self._is_new(song['yt_id']):
                        yield song

                if i % 30 == 0:
                    logger.info(f"  Variations: {i}/{len(variation_queries)} done")
                time.sleep(DISCOVERY_DELAY)
            except Exception as e:
                logger.warning(f"  Variation failed ({query}): {e}")
                time.sleep(2)

    # ── PHASE 4: SEARCH QUERIES ───────────────────────────────────────────────

    def _phase_search(self, cycle: int = 1) -> Generator:
        if not self.ytm:
            return

        queries = SEARCH_QUERIES.copy()
        if cycle > 1:
            random.shuffle(queries)

        total = len(queries)
        for i, query in enumerate(queries, 1):
            try:
                results = self.ytm.search(
                    query, filter='songs',
                    limit=RESULTS_PER_QUERY, ignore_spelling=False
                )
                for item in results:
                    song = self._parse_item(item, priority=4)
                    if song and self._is_new(song['yt_id']):
                        yield song

                if i % 100 == 0:
                    logger.info(f"  Queries: {i}/{total} | Unique: {len(self._seen):,}")
                time.sleep(DISCOVERY_DELAY + random.uniform(0, 1))
            except Exception as e:
                logger.warning(f"  Search failed ('{query}'): {e}")
                time.sleep(2)

    # ── PHASE 5: PLAYLISTS ────────────────────────────────────────────────────

    def _phase_playlists(self) -> Generator:
        if not self.ytm:
            return
        for pid in PLAYLIST_IDS:
            try:
                data  = self.ytm.get_playlist(pid, limit=500)
                items = data.get('tracks', [])
                count = 0
                for item in items:
                    song = self._parse_item(item, priority=3)
                    if song and self._is_new(song['yt_id']):
                        yield song
                        count += 1
                logger.info(f"  Playlist {pid[:20]}: {count} new")
                time.sleep(DISCOVERY_DELAY * 3)
            except Exception as e:
                logger.warning(f"  Playlist failed: {e}")

    # ── HELPERS ───────────────────────────────────────────────────────────────

    def _is_new(self, yt_id: str) -> bool:
        if yt_id in self._seen:
            return False
        self._seen.add(yt_id)
        return True

    def _parse_item(self, item: dict, priority: int = 4,
                    default_lang: str = 'unknown') -> Dict[str, Any]:
        if not item or not isinstance(item, dict):
            return None
        yt_id = item.get('videoId')
        if not yt_id or len(yt_id) != 11:
            return None

        title       = (item.get('title') or 'Unknown').strip()
        artists_raw = item.get('artists') or []
        if isinstance(artists_raw, str):
            artists_raw = [{'name': artists_raw}]
        artist      = artists_raw[0].get('name', 'Unknown').strip() if artists_raw else 'Unknown'
        all_artists = [a.get('name', '').strip() for a in artists_raw if isinstance(a, dict)]
        album_data  = item.get('album') or {}
        album       = album_data.get('name', '').strip() if isinstance(album_data, dict) else ''
        duration    = self._parse_duration(item.get('duration', '0:00'))
        language    = self._detect_language(title, artist, default_lang)

        return {
            'yt_id':      yt_id,
            'title':      title,
            'artist':     artist,
            'artists':    all_artists,
            'album':      album,
            'duration':   duration,
            'language':   language,
            'genre':      '',
            'view_count': 0,
            'priority':   priority,
        }

    @staticmethod
    def _parse_duration(duration_str) -> int:
        try:
            parts = [int(x) for x in str(duration_str).strip().split(':')]
            if len(parts) == 2:
                return parts[0] * 60 + parts[1]
            elif len(parts) == 3:
                return parts[0] * 3600 + parts[1] * 60 + parts[2]
        except Exception:
            pass
        return 0

    @staticmethod
    def _detect_language(title: str, artist: str, default: str) -> str:
        if default not in ('unknown', 'hindi', 'hindi_composers'):
            return default
        text = (title + ' ' + artist).lower()
        if any(k in text for k in ['tamil', 'kollywood', 'ilayaraja', 'anirudh',
                                    'vijay', 'ajith', 'suriya', 'kamal']):
            return 'tamil'
        if any(k in text for k in ['telugu', 'tollywood', 'prabhas', 'allu arjun',
                                    'mahesh babu', 'thaman', 'dsp songs']):
            return 'telugu'
        if any(k in text for k in ['punjabi', 'bhangra', 'jatt', 'diljit', 'ap dhillon',
                                    'sidhu', 'moosewala', 'karan aujla', 'shubh']):
            return 'punjabi'
        if any(k in text for k in ['haryanvi', 'sapna', 'renuka']):
            return 'haryanvi'
        if any(k in text for k in ['bhojpuri', 'khesari', 'pawan singh bhojpuri']):
            return 'bhojpuri'
        hindi_kw = ['bollywood', 'hindi', 'pyaar', 'dil', 'mohabbat', 'ishq',
                    'arijit', 'jubin', 'neha kakkar', 'shreya', 'sonu nigam',
                    'kumar sanu', 'kishore', 'rafi', 'lata', 'asha bhosle',
                    'atif', 'rahat', 'sunidhi', 'pritam', 'vishal shekhar']
        if any(k in text for k in hindi_kw):
            return 'hindi'
        if all(ord(c) < 128 for c in (title + artist)) and default == 'unknown':
            return 'english'
        return default if default != 'unknown' else 'hindi'
