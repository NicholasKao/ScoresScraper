# coding: utf-8
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from datetime import datetime as dt
from datetime import timedelta as td
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
import pandas as pd
import numpy as np
import configparser
import time
import calendar
import pymysql


class ANScraper:

    def __init__(self, config_file='config.txt'):

        # Load and read config
        self.config = configparser.RawConfigParser()
        self.config.read(config_file)

        # Create Chrome driver instance
        option = webdriver.ChromeOptions()
        option.add_argument(" — incognito")
        self.browser = webdriver.Chrome(ChromeDriverManager().install())

    def login(self):
        # Logging In
        self.browser.get('https://www.actionnetwork.com/login')
        self.browser.find_element_by_id("email").send_keys(
            self.config.get('ActionNetwork', 'email'))
        self.browser.find_element_by_id("password").send_keys(
            self.config.get('ActionNetwork', 'password'))
        self.browser.find_element_by_id('login-submit').click()
        # Wait for new page to load before moving on to make sure page loaded
        time.sleep(2)

    def quit(self):
        self.browser.quit()

    def scrape_data(self, date, options=[], backfilling = False):
        day_dict = {'Mon':'Monday','Tue':'Tuesday', 'Wed':'Wednesday','Thu':'Thursday','Fri':'Friday','Sat':'Saturday','Sun':'Sunday'}
        month_dict = {'Jan':1,'Feb':2,'Mar':3, 'Apr':4, 'May':5, 'Jun':6, 'Jul':7, 'Aug':8, 'Sep':9, 'Oct':10, 'Nov':11, 'Dec':12}
        time.sleep(2)
        # Scrape the Header and Spreads Table
        odds_data = []
        try:
            odds_table = self.browser.find_element_by_tag_name('tbody')
            table_rows = odds_table.find_elements_by_tag_name('tr')
            for row in table_rows:
                try:
                    game_data = {}
                    game_info = row.find_element_by_class_name('public-betting__game-info').text.split('\n')
                    if game_info[0] == 'PPD':
                        game_data['WeekDay'] = 'PPD'
                        game_data['Month'] = 'PPD'
                        game_data['Day'] = 'PPD'
                        game_data['Time'] = 'PPD'
                        game_data['Year'] = 'PPD'
                        game_data['AwayRot'] = None
                        game_data['AwayTeam'] = game_info[1]
                        game_data['HomeRot'] = None
                        game_data['HomeTeam'] = game_info[2]
                        continue
                    elif game_info[0] == 'CANCELLED':
                        game_data['WeekDay'] = 'PPD'
                        game_data['Month'] = 'PPD'
                        game_data['Day'] = 'PPD'
                        game_data['Time'] = 'PPD'
                        game_data['Year'] = 'PPD'
                        if len(game_info) == 3:
                            game_data['AwayRot'] = None
                            game_data['AwayTeam'] = game_info[1]
                            game_data['HomeRot'] = None
                            game_data['HomeTeam'] = game_info[2]
                        else:
                            game_data['AwayRot'] = game_info[1]
                            game_data['AwayTeam'] = game_info[2]
                            game_data['HomeRot'] = game_info[3]
                            game_data['HomeTeam'] = game_info[4]
                        continue
                    elif game_info[0] == 'TBD':
                        game_data['WeekDay'] = 'TBD'
                        game_data['Month'] = 'TBD'
                        game_data['Day'] = 'TBD'
                        game_data['Time'] = 'TBD'
                        game_data['Year'] = 'TBD'
                        if len(game_info) == 3:
                            game_data['AwayRot'] = None
                            game_data['AwayTeam'] = game_info[1]
                            game_data['HomeRot'] = None
                            game_data['HomeTeam'] = game_info[2]
                        else:
                            game_data['AwayRot'] = game_info[1]
                            game_data['AwayTeam'] = game_info[2]
                            game_data['HomeRot'] = game_info[3]
                            game_data['HomeTeam'] = game_info[4]
                    else:
                        try:
                            if backfilling:
                                game_data['WeekDay'] = day_dict[date.split(' ')[0]]
                                game_data['Month'] = month_dict[date.split(' ')[1]]
                                game_data['Day'] = pd.to_numeric(date.split(' ')[2])
                                game_data['Time'] = game_info[0].split(', ')[1]
                            else:
                                game_data['WeekDay'] = day_dict[game_info[0].split(' ')[0]]
                                game_data['Month'] = game_info[0].split(',')[0].split(' ')[1].split('/')[0]
                                game_data['Day'] = game_info[0].split(',')[0].split(' ')[1].split('/')[1]
                                game_data['Time'] = game_info[0].split(', ')[1]
                        except Exception as e: ## error occurs when game is current day
                            game_data['WeekDay'] = calendar.day_name[dt.today().weekday()]
                            game_data['Month'] = dt.today().date().month
                            game_data['Day'] = dt.today().date().day
                            game_data['Time'] = game_info[0]
                        game_data['Year'] = dt.today().date().year ## fix this, need to grab actual year
                        if len(game_info) == 3:
                            game_data['AwayRot'] = None
                            game_data['AwayTeam'] = game_info[1]
                            game_data['HomeRot'] = None
                            game_data['HomeTeam'] = game_info[2]
                        else:
                            game_data['AwayRot'] = game_info[2]
                            game_data['AwayTeam'] = game_info[1]
                            game_data['HomeRot'] = game_info[4]
                            game_data['HomeTeam'] = game_info[3]

                    try:
                        open_info = row.find_element_by_class_name('public-betting__open-container').text
                        game_data[f'{options[0][0]}Open'] = open_info.split('\n')[0].replace('+','').replace('PK','0')
                        game_data[f'{options[0][1]}Open'] = open_info.split('\n')[1].replace('+','').replace('PK','0')
                    except:
                        game_data[f'{options[0][0]}Open'] = None
                        game_data[f'{options[0][1]}Open'] = None
                        game_data[f'CurrentBest{options[0][0]}Line'] = None
                        game_data[f'CurrentBest{options[0][1]}Line'] = None
                        game_data[f'CurrentBest{options[0][0]}LineJuice'] = None
                        game_data[f'CurrentBest{options[0][1]}LineJuice'] = None
                        game_data[f'{options[0][0]}Ticket%'] = None
                        game_data[f'{options[0][1]}Ticket%'] = None
                        game_data[f'{options[0][0]}Money%'] = None
                        game_data[f'{options[0][1]}Money%'] = None
                        game_data['TicketCount'] = None
                        odds_data.append(game_data)
                        continue

                    try:
                        current_odds = row.find_element_by_class_name('public-betting__odds-container').text
                        game_data[f'CurrentBest{options[0][0]}Line'] = current_odds.split('\n')[0].replace('+','').replace('PK','0')
                        game_data[f'CurrentBest{options[0][1]}Line'] = current_odds.split('\n')[2].replace('+','').replace('PK','0')
                        if options[0] != ['AwayML','HomeML']:
                            game_data[f'CurrentBest{options[0][0]}LineJuice'] = current_odds.split('\n')[1].replace('+','')
                            game_data[f'CurrentBest{options[0][1]}LineJuice'] = current_odds.split('\n')[3].replace('+','')
                    except:
                        game_data[f'CurrentBest{options[0][0]}Line'] = None
                        game_data[f'CurrentBest{options[0][1]}Line'] = None
                        if options[0] != ['AwayML','HomeML']:
                            game_data[f'CurrentBest{options[0][0]}LineJuice'] = None
                            game_data[f'CurrentBest{options[0][1]}LineJuice'] = None
                    try:
                        ticket_data = row.find_elements_by_class_name('public-betting__percents-container')[0].text
                        game_data[f'{options[0][0]}Ticket%'] = ticket_data.split('\n')[0].replace('%','')
                        game_data[f'{options[0][1]}Ticket%'] = ticket_data.split('\n')[1].replace('%','')
                    except:
                        game_data[f'{options[0][0]}Ticket%'] = None
                        game_data[f'{options[0][1]}Ticket%'] = None

                    try:
                        money_data = row.find_elements_by_class_name('public-betting__percents-container')[1].text
                        game_data[f'{options[0][0]}Money%'] = money_data.split('\n')[0].replace('%','')
                        game_data[f'{options[0][1]}Money%'] = money_data.split('\n')[1].replace('%','')
                    except:
                        game_data[f'{options[0][0]}Money%'] = None
                        game_data[f'{options[0][1]}Money%'] = None

                    game_data['TicketCount'] = row.find_element_by_class_name('public-betting__number-of-bets').text.replace(',','')
                    if game_data['TicketCount'] == 'N/A':
                        game_data['TicketCount'] = None

                    odds_data.append(game_data)
                except Exception as e:
                    print(e)
        except NoSuchElementException as e:
            print('No Data Present')
            #print(f'\t{e}')
            return([])
        return(odds_data)

    def join_data(self, spreads, totals, mls, options = []):
        spread_data = pd.DataFrame(spreads)
        spread_data = pd.DataFrame(spreads)
        total_data = pd.DataFrame(totals)
        ml_data = pd.DataFrame(mls)
        total_data['TicketCount'] = spread_data['TicketCount']
        ml_data['TicketCount'] = spread_data['TicketCount']
        odds_table = spread_data.merge(total_data, how = 'outer', on=['WeekDay','Month','Day','Time','Year','AwayRot','AwayTeam','HomeRot','HomeTeam','TicketCount']).merge(ml_data, how = 'outer', on=['WeekDay','Month','Day','Time','Year','AwayRot','AwayTeam','HomeRot','HomeTeam','TicketCount'])
        odds_table['Closed'] = np.where(odds_table['Time'].str.contains('PM') | odds_table['Time'].str.contains('AM'), 'No','Yes')
        return(odds_table)
    
    
    def scrape_odds(self, league, backfill = False):
        self.browser.get(f'https://www.actionnetwork.com/{league}/public-betting')
        page_date = self.browser.find_element_by_class_name
        
        if backfill:
            while backfill:
                try:
                    buttons = self.browser.find_elements_by_class_name("day-nav__button")
                    if len(buttons) == 2:
                        buttons[0].click()
                        page_date = self.browser.find_element_by_class_name("day-nav__display").text
                        print(page_date)
                        self.into_db(self.scrape_line_types(page_date, league), league)
                    else:
                        break
                except Exception as e:
                    print(e)
                    break
        else:
            self.into_db(self.scrape_line_types(page_date, league), league)
                
    def scrape_line_types(self, date, league):
        line_types = self.browser.find_elements_by_class_name("odds-tools-sub-nav__non-filter-component.custom-1grr0s4.ex4wozm1")[1]
        line_types_selector = Select(line_types.find_element_by_tag_name('select'))
        ## For defaulting to spread data being already clicked
        if league in ['nfl','ncaaf','ncaab','nba']:
            line_types_selector.select_by_value('spread')
            spread_data = self.scrape_data(date, [['Away','Home']])
            line_types_selector.select_by_value('total')
            total_data = self.scrape_data(date, [['Over','Under']])
            line_types_selector.select_by_value('ml')
            ml_data = self.scrape_data(date, [['AwayML','HomeML']])
        elif league in ['mlb','nhl']:
            line_types_selector.select_by_value('ml')
            ml_data = self.scrape_data(date, [['AwayML','HomeML']])
            line_types_selector.select_by_value('spread')
            spread_data = self.scrape_data(date, [['Away','Home']])
            line_types_selector.select_by_value('total')
            total_data = self.scrape_data(date, [['Over','Under']])
        if spread_data:
            return(self.join_data(spread_data, total_data, ml_data))
        else:
            return(pd.DataFrame([]))
    
    def into_db(self, df, table, data = 'odds'):
        connection = pymysql.connect(user = 'root', password = 'sports4ever!M',host = '127.0.0.1', database = 'ActionNetwork')
        if data == 'odds':
            if not df.empty:
                #connection = pymysql.connect(user = self.config.get('an','user'), password = self.config.get('an','password'), host = self.config.get('an','host'), database = 'ActionNetwork')
                with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                    query = f"""SELECT * FROM {table} WHERE Closed = 'Yes'"""
                    cursor.execute(query)
                closed_data = cursor.fetchall()
                if len(closed_data) > 0:
                    previously_closed = pd.DataFrame(closed_data)
                else:
                    previously_closed = pd.DataFrame([])
                with connection.cursor() as cursor:
                    for idx, row in df.iterrows():
                        if not previously_closed.empty and len(previously_closed[(previously_closed['Month'] == int(row['Month'])) & (previously_closed['Day'] == int(row['Day'])) & (previously_closed['Year'] == int(row['Year'])) & (previously_closed['HomeTeam'] == (row['HomeTeam'])) & (previously_closed['Closed'] == 'Yes')]) > 0:
                            continue
                        else:
                            try:
                                if not pd.isna(row['OverOpen']):
                                    row['OverOpen'] = row['OverOpen'][1:] #remove the prepended "o" from the line
                                if not pd.isna(row['CurrentBestOverLine']):
                                    row['CurrentBestOverLine'] = row['CurrentBestOverLine'][1:]
                                if not pd.isna(row['CurrentBestUnderLine']):
                                    row['CurrentBestUnderLine'] = row['CurrentBestUnderLine'][1:]

                                values = f"""'{row['Month']}', '{row['Day']}', '{row['Year']}', '{row['WeekDay']}', '{row['Time']}', '{row['AwayRot']}', "{row['AwayTeam']}", '{row['HomeRot']}', "{row['HomeTeam']}", '{row['AwayOpen']}', '{row['HomeOpen']}', '{row['CurrentBestAwayLine']}', '{row['CurrentBestAwayLineJuice']}', '{row['CurrentBestHomeLine']}', '{row['CurrentBestHomeLineJuice']}', '{row['AwayTicket%']}', '{row['AwayMoney%']}', '{row['HomeTicket%']}', '{row['HomeMoney%']}', '{row['OverOpen']}', '{row['CurrentBestOverLine']}', '{row['CurrentBestOverLineJuice']}', '{row['CurrentBestUnderLine']}', '{row['CurrentBestUnderLineJuice']}', '{row['OverTicket%']}', '{row['OverMoney%']}', '{row['UnderTicket%']}', '{row['UnderMoney%']}', '{row['AwayMLOpen']}', '{row['HomeMLOpen']}', '{row['CurrentBestAwayMLLine']}', '{row['CurrentBestHomeMLLine']}', '{row['AwayMLTicket%']}', '{row['AwayMLMoney%']}', '{row['HomeMLTicket%']}', '{row['HomeMLMoney%']}', '{row['TicketCount']}', '{dt.now()}', NULL, '{row['Closed']}'""".replace( "'None'","NULL").replace("'nan'",'NULL')

                                query = f"""INSERT INTO {table} VALUES ({values});"""
                                cursor.execute(query)
                            except Exception as e:
                                print(e)
                                print(row)
                connection.commit()
        elif data == 'scores':
            if not df.empty:
                with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                    query = f"""SELECT * FROM {table}"""
                    cursor.execute(query)
                existing_scores = cursor.fetchall()
                if len(existing_scores) > 0:
                    score_data = pd.DataFrame(existing_scores)
                else:
                    score_data = pd.DataFrame([])
                with connection.cursor() as cursor:
                    for idx, row in df.iterrows():
                        if not score_data.empty and len(score_data[(score_data['GameDate'] == row['Date']) & (score_data['AwayTeam'] == row['AwayTeam'])]) > 0:
                            continue
                        try:
                            values = f"""'{row['Date']}', '{row['AwayRot']}', "{row['AwayTeam']}", '{row['AwayScore']}', '{row['HomeRot']}', "{row['HomeTeam']}", '{row['HomeScore']}'""".replace( "'None'","NULL").replace("'nan'",'NULL')

                            query = f"""INSERT INTO {table} VALUES ({values});"""
                            cursor.execute(query)
                        except Exception as e:
                            print(e)
                            print(row)
                connection.commit()
        connection.close()
            
    def scrape_previous_scores(self, league, backfill_date = None):
        # lists and dicts needed for lookups and relative references
        weeks = {'NFL': ['Hall of Fame Weekend','Preseason Week 1','Preseason Week 2','Preseason Week 3','Week 1','Week 2','Week 3','Week 4','Week 5','Week 6','Week 7','Week 8','Week 9','Week 10','Week 11','Week 12','Week 13','Week 14','Week 15','Week 16','Week 17','Week 18','Wild Card','Division Round','Conf Champ','Pro Bowl','Super Bowl'],
                 'NCAAF': ['Week 1','Week 2','Week 3','Week 4','Week 5','Week 6','Week 7','Week 8','Week 9','Week 10','Week 11','Week 12','Week 13','Week 14','Week 15','Bowls']}
        # navigate to league odds page
        self.browser.get(f'https://www.actionnetwork.com/{league}/odds')
        # go back one day - doesn't work for football since it uses weeks
        if league in ['NFL','NCAAF']:
            filters = self.browser.find_element_by_class_name('odds-tools-sub-nav__odds-settings')
            filters.click()
            week_selector = Select(self.browser.find_element_by_class_name('odds-tools-sub-nav__date.custom-1grr0s4.ex4wozm1')
            .find_element_by_tag_name('select'))
            selected_week = week_selector.first_selected_option.text.title()
            selected_week_index = weeks[league].index(selected_week)
            previous_date = weeks[league][selected_week_index - 1]
            week_selector.select_by_value(previous_date)
            selected_week_index -= 1
        else:
            filters = self.browser.find_element_by_class_name('odds-tools-sub-nav__odds-settings')
            filters.click()
            self.browser.find_element_by_class_name('day-nav__button.custom-1nzrqwz.e1y7ccqs0').click()
            previous_date = dt.today().date() - td(days = 1)
        previous_scores = self.get_scores(previous_date)
        self.into_db(previous_scores, f'{league}_Scores', 'scores')
        
        if backfill_date:
            backfill_date = pd.to_datetime(backfill_date)
            if league in ['NFL','NCAAF']:
                while selected_week_index > 0:
                    previous_date = weeks[league][selected_week_index - 1]
                    print(previous_date)
                    week_selector.select_by_value(previous_date)
                    time.sleep(2)
                    selected_week_index -= 1
                    prev_scores = self.get_scores(previous_date)
                    self.into_db(prev_scores, f'{league}_Scores', 'scores')
            else:
                while previous_date > backfill_date:
                    # scroll back up and change the date to previous day
                    self.browser.execute_script("window.scrollTo(document.body.scrollHeight,0);")
                    time.sleep(2)
                    self.browser.find_element_by_class_name('day-nav__button.custom-1nzrqwz.e1y7ccqs0').click()
                    time.sleep(2)
                    previous_date = previous_date - td(days = 1)
                    print(previous_date)
                    prev_scores = self.get_scores(previous_date)
                    self.into_db(prev_scores, f'{league}_Scores', 'scores')
                
    def get_scores(self, date):
        self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        # sleeping in order to handle lazy loading of new table data
        time.sleep(2)
        away_teams = []
        home_teams = []
        away_rots = []
        home_rots = []
        away_scores = []
        home_scores = []
        # get table with score data
        try:
            scores_table = self.browser.find_element_by_class_name('best-odds__table-container').find_element_by_tag_name('tbody')
        except NoSuchElementException as e:
            print(f'No data for {date}')
            return(pd.DataFrame([]))
        table_rows = scores_table.find_elements_by_tag_name('tr')
        game_rows = table_rows[::2]
        status_rows = table_rows[1::2]
        for game, status in list(zip(game_rows, status_rows)):
            if status.text.lower() != 'final': #game not over
                continue
            team_info = game.find_element_by_class_name('best-odds__game-info').find_elements_by_class_name('game-info__teams')
            away_team = team_info[0].find_element_by_class_name('game-info__team').find_element_by_class_name('game-info__team--mobile').text
            away_rot = team_info[0].find_element_by_class_name('game-info__team').find_element_by_class_name('game-info__rot-number').text
            away_score = team_info[0].find_element_by_class_name('game-info__score').text

            home_team = team_info[1].find_element_by_class_name('game-info__team').find_element_by_class_name('game-info__team--mobile').text
            home_rot = team_info[1].find_element_by_class_name('game-info__team').find_element_by_class_name('game-info__rot-number').text
            home_score = team_info[1].find_element_by_class_name('game-info__score').text

            away_teams.append(away_team)
            home_teams.append(home_team)
            away_rots.append(away_rot)
            home_rots.append(home_rot)
            away_scores.append(away_score)
            home_scores.append(home_score)

        # for row in table_rows:
        #     self.browser.execute_script("return arguments[0].scrollIntoView();", row)
        #     game_info = row.find_element_by_class_name('best-odds__game-info')
        #     print(game_info.text)
            # game_status = row.find_element_by_class_name('best-odds__game-status').text
            # if 'final' not in game_status.lower():
            #     continue
            # try:
            #     team_names = row.find_elements_by_class_name('game-info__team--desktop')
            #     away_teams.append(team_names[0].text)
            #     home_teams.append(team_names[1].text)
            # except:
            #     # need some way to notify that this entry failed
            #     continue
            # try:
            #     team_rots = row.find_elements_by_class_name('game-info__rot-number')
            #     away_rots.append(team_rots[0].text)
            #     home_rots.append(team_rots[1].text)
            # except StaleElementReferenceException:
            #     # remove previously added data for this row
            #     # still need some way to notify this entry failed
            #     away_teams = away_teams[:-1]
            #     home_teams = home_teams[:-1]
            #     continue
            # except IndexError:
            #     away_rots.append(None)
            #     home_rots.append(None)
            # try:
            #     team_scores = row.find_elements_by_class_name('game-info__score')
            #     away_scores.append(team_scores[0].text)
            #     home_scores.append(team_scores[1].text)
            # except StaleElementReferenceException:
            #     # remove previously added data for this row
            #     # still need some way to notify this entry failed
            #     away_teams = away_teams[:-1]
            #     home_teams = home_teams[:-1]
            #     away_rots = away_rots[:-1]
            #     home_rots = home_rots[:-1]
            #     continue
        previous_scores = pd.DataFrame(data = {'Date': [date for x in away_rots],
                                           'AwayRot': away_rots,
                                           'AwayTeam': away_teams,
                                           'AwayScore': away_scores,
                                           'HomeRot': home_rots,
                                           'HomeTeam': home_teams,
                                           'HomeScore': home_scores})
        return(previous_scores)
                
                
if __name__ == "__main__":
    scraper = ANScraper()
    scraper.login()

    scraper.scrape_previous_scores('NBA')
    scraper.scrape_odds('nba')
    scraper.scrape_previous_scores('NFL')
    scraper.scrape_odds('nfl')
    scraper.scrape_previous_scores('NCAAF')
    scraper.scrape_odds('ncaaf')
    scraper.scrape_previous_scores('NCAAB')
    scraper.scrape_odds('ncaab')
    scraper.scrape_previous_scores('NHL')
    scraper.scrape_odds('nhl')
    scraper.scrape_previous_scores('MLB')
    scraper.scrape_odds('mlb')
    scraper.quit()