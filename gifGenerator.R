# install.packages("devtools")

# devtools::install_github("thomasp85/gganimate")
# devtools::install_github("thomasp85/transformr")


library(tidyverse)
library(ggplot2)
library(gganimate)
library(scales)
library(ggthemes)
library(hrbrthemes)

theme_set(hrbrthemes::theme_ipsum())

aapl <- read_csv('/Users/spencerbraun/dev/repos/active_portfolio_mgmt/data/stocks/AAPL.csv')

aapl %>% ggplot(aes(x = Date, y= Close)) +
  geom_line() +
  ggtitle("{frame_time}") +
  transition_time(Date) +
  shadow_mark(past = TRUE, future = FALSE)


daily <- read_csv('/Users/spencerbraun/dev/repos/market_gifs/data_20200716/SPCE_daily_1594930040.632224.csv')
intraday <- read_csv('/Users/spencerbraun/dev/repos/market_gifs/data_20200716/SPCE_intraday_1594930040.632224.csv')
intraday_path = '/Users/spencerbraun/dev/repos/market_gifs/data_20200716/SPCE_intraday_1594930040.632224.csv'
symbol <- str_split(basename(intraday_path), "_")[[1]][1]
today <- Sys.Date()
date_formatted <- format(today, format="%B %d %Y")

daily %>% ggplot(aes(x = date, y= close)) +
  geom_line() +
  labs(x="Date", y="", title=str_interp("${symbol} Daily {frame_along}"))  +
  transition_reveal(date)


intradayPlot <- intraday %>% ggplot() +
  geom_line(aes(x=time, y=close)) +
  labs(x="Time", y="", title=str_interp("${symbol}"),
       subtitle=str_interp("Intraday {frame_along}")) +
  transition_reveal(time)



animate(intradayPlot, height = 800, width =1600)
anim_save(str_interp("${symbol}_intraday_${today}.gif"))
