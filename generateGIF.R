library(tidyverse)
library(ggplot2)
library(gganimate)
library(scales)
library(ggthemes)
library(hrbrthemes)
library(lubridate)


theme_set(hrbrthemes::theme_ipsum())

today <- today()
date_named <- format(today, format="%B %d %Y")
date_str <- format(today, format="%Y%m%d")

today_dir <- str_interp('data_${date_str}')
files <- list.files(today_dir)

name <- read_file(str_interp('${today_dir}/name.csv'))

daily_path <- files[str_detect(files, "daily")]
intr_path <- files[str_detect(files, "intraday")]

daily <- read_csv(str_interp('${today_dir}/${daily_path}'))
intraday <- read_csv(str_interp('${today_dir}/${intr_path}'))

symbol <- str_split(basename(intr_path), "_")[[1]][1]


dailyPlot <- daily %>% ggplot(aes(x = date, y= close)) +
  geom_line() +
  labs(x="Date", y="", title=str_interp("${name}"),
       subtitle=str_interp("${symbol} Daily {frame_along}")) +
  transition_reveal(date)


intradayPlot <- intraday %>% ggplot() +
  geom_line(aes(x=time, y=close)) +
  labs(x="Time", y="", title=str_interp("${name}"),
       subtitle=str_interp("${symbol} Intraday {intraday$time[which(intraday$time == frame_along)]}")) +
  transition_reveal(time)

tail(intraday)

animate(intradayPlot, height=400, width=800)
anim_save(str_interp("${today_dir}/${symbol}_intraday_${today}.gif"))

animate(dailyPlot, height=400, width=800)
anim_save(str_interp("${today_dir}/${symbol}_daily_${today}.gif"))
