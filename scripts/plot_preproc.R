
library(colormap)
library(ggpubr)
library(ggplot2)
library(RColorBrewer)
library(directlabels)
library(colorRamps)
library(scales)
library(tools)
library(patchwork)
library(ggrepel)
library(dplyr)
library(zoo)
library(grid)
library(stats)
library(data.table)
library(DescTools)
library(oce)
library(tidyr) # for separate
library(stringr) # Load stringr

options(digits = 5)
text_size = 9
line_thickness = 0.25
inch_converting =  2.54



wd_path <- "D:/TUD/ReviewPaper/historic_air_photos/figures/preproc/"
reviewSheet <- "D:/TUD/ReviewPaper/historic_air_photos/data/Review_Historic_Air_Photos.csv"



myData = read.csv(file = reviewSheet, header = TRUE, sep = "," ,na.strings=c("","NA"))

myData$Pre.processing[is.na(myData$Pre.processing)] <- "not specified"
myData$simplified.geometric.preprocessing[is.na(myData$simplified.geometric.preprocessing)] <- "NA"
myData$simplified.radiometric.preprocessing[is.na(myData$simplified.radiometric.preprocessing)] <- "NA"
myData$Pre.processing <- factor(myData$Pre.processing)
myData$simplified.geometric.preprocessing <- factor (myData$simplified.geometric.preprocessing)
myData$simplified.radiometric.preprocessing <- factor (myData$simplified.radiometric.preprocessing)



perc_no_preproc = 100 * sum(myData$Pre.processing == "no") / length(myData$Pre.processing)
perc_notspec_preproc = 100 * sum(myData$Pre.processing == "not specified") / length(myData$Pre.processing)
perc_preproc = 100 * sum(myData$Pre.processing == "yes") / length(myData$Pre.processing)

print(paste("Number of datasets using preprocessing: ",  sum(myData$Pre.processing == "yes") , "(",perc_preproc,"%)"))
print(paste("Number of datasets not using preprocessing: ", sum(myData$Pre.processing == "no") , "(",perc_no_preproc,"%)"))
print(paste("Number of datasets preprocessing is not specified: ", sum(myData$Pre.processing == "not specified") , "(",perc_notspec_preproc,"%)"))
print(paste("Total number of datasets in table: ", length(myData$Pre.processing)))


perc_preproc_radio = 100 * sum(!myData$simplified.radiometric.preprocessing == "NA" & myData$simplified.geometric.preprocessing == "NA") /  sum(myData$Pre.processing == "yes") # radio only
perc_preproc_geom = 100 * sum(!myData$simplified.geometric.preprocessing == "NA" & myData$simplified.radiometric.preprocessing == "NA") /  sum(myData$Pre.processing == "yes") # geom only
perc_preproc_both = 100 * sum(!myData$simplified.geometric.preprocessing == "NA" & !myData$simplified.radiometric.preprocessing == "NA") /  sum(myData$Pre.processing == "yes")

no_preproc_radio = sum(!myData$simplified.radiometric.preprocessing == "NA" & myData$simplified.geometric.preprocessing == "NA") 
no_preproc_geom = sum(!myData$simplified.geometric.preprocessing == "NA" & myData$simplified.radiometric.preprocessing == "NA") 
no_preproc_both = sum(!myData$simplified.radiometric.preprocessing == "NA" & !myData$simplified.geometric.preprocessing == "NA") 

print(paste("Number of datasets using radiometric preprocessing: ",  no_preproc_radio, "/", sum(myData$Pre.processing == "yes") , "(",perc_preproc_radio,"%)"))
print(paste("Number of datasets using geometric preprocessing: ",  no_preproc_geom, "/", sum(myData$Pre.processing == "yes") , "(",perc_preproc_geom,"%)"))
print(paste("Number of datasets using both types of preprocessing: ",  no_preproc_both, "/", sum(myData$Pre.processing == "yes") , "(",perc_preproc_both,"%)"))


# create pie chart - Pre-processing done in percentage
# Create Data
perc_preproc_labels <- c("no", "yes", "not specified")
perc_preproc_vals <- c(perc_no_preproc, perc_preproc, perc_notspec_preproc)

# Compute the position of labels

perc_preproc_data <- data.frame(perc_preproc_labels, perc_preproc_vals)
perc_preproc_data <- perc_preproc_data %>% 
  arrange(desc(perc_preproc_labels)) %>%
  mutate(prop = perc_preproc_vals / sum(perc_preproc_data$perc_preproc_vals) *100) %>%
  mutate(ypos = cumsum(prop)- 0.5*prop )

# Basic piechart
plt_preproc_data <- ggplot(perc_preproc_data, aes(x="", y=prop, fill=perc_preproc_labels)) +
  geom_bar(stat="identity", width=1, color="white") +
  coord_polar("y", start=0) +
  #theme_void() + 
  theme(legend.position="none", plot.title = element_text(color="black", hjust=0.5), text = element_text(size = 20)) +
  geom_text(aes(y = ypos, label = perc_preproc_labels), color = "white", size=5) +
  labs(title="", x ="", y="")

png(paste(wd_path, "Rplot_img_preproc.png"), units="in", width=5, height=5, res=300) #print
plot(plt_preproc_data)
dev.off()


# create pie chart - Types of Pre-processing done in percentage
# Create Data
perc_preproc_types_labels <- c("geom", "radiom", "both")
perc_preproc_types_vals <- c(perc_preproc_geom, perc_preproc_radio, perc_preproc_both)

# Compute the position of labels

perc_preproc_types_data <- data.frame(perc_preproc_types_labels, perc_preproc_types_vals)
perc_preproc_types_data <- perc_preproc_types_data %>% 
  arrange(desc(perc_preproc_types_labels)) %>%
  mutate(prop = perc_preproc_types_vals / sum(perc_preproc_types_data$perc_preproc_types_vals) *100) %>%
  mutate(ypos = cumsum(prop)- 0.5*prop)

# Basic piechart
plt_preproc_types_data <- ggplot(perc_preproc_types_data, aes(x="", y=prop, fill=perc_preproc_types_labels)) +
  geom_bar(stat="identity", width=1, color="white") +
  coord_polar("y", start=0) +
  #theme_void() + 
  theme(legend.position="none", plot.title = element_text(color="black", hjust=0.5), text = element_text(size = 20)) +
  geom_text(aes(y = ypos, label = perc_preproc_types_labels), color = "white", size=5) +
  labs(title="", x ="", y="")

png(paste(wd_path, "Rplot_img_preproc_types.png"), units="in", width=5, height=5, res=300) #print
plot(plt_preproc_types_data)
dev.off()












# make it simpler and create a sub data frame
mD_Key  <- myData$Key
mD_preproc <- myData$Pre.processing
mD_preproc_geom  <- myData$simplified.geometric.preprocessing
mD_preproc_radio  <- myData$simplified.radiometric.preprocessing
df_preproc <- data.frame('key' = mD_Key, 'PreProc' = mD_preproc, 'Geom' = mD_preproc_geom, "Radio" = mD_preproc_radio)

df_preproc$PreProc <- factor (df_preproc$PreProc)
# remove rows where Pre.processing = "not specified" or "no"

df_preproc <- df_preproc[!(df_preproc$PreProc=="not specified" | df_preproc$PreProc=="no"),]
df_preproc$PreProc <- NULL #df contains only datasets that have been preprocessed. no need to keep "preprocessing" column 

# melt by key
df_preproc_melt <- melt(df_preproc, id = 'key')
# split by geometric and radiometric preprocessing
df_preproc_melt_geom <- df_preproc_melt[(df_preproc_melt$variable=="Geom"),]
df_preproc_melt_radio <- df_preproc_melt[(df_preproc_melt$variable=="Radio"),]

df_preproc_melt_geom$variable <- NULL #entry no longer needed
df_preproc_melt_radio$variable <- NULL


df_preproc_melt_radio <- df_preproc_melt_radio[!(df_preproc_melt_radio$value=="NA"),] # clear NA vals
df_preproc_melt_radio_sep <- separate(data = df_preproc_melt_radio, col = value, into = c("val1", "val2", "val3", "val4", "val5"), sep = ",")
df_preproc_melt_radio_sep <- melt(df_preproc_melt_radio_sep, id = 'key')
df_preproc_melt_radio_sep$variable <- NULL
df_preproc_melt_radio_sep <- df_preproc_melt_radio_sep[!is.na(df_preproc_melt_radio_sep$value),] #delete NA vals
df_preproc_melt_radio_sep$value <- as.character (df_preproc_melt_radio_sep$value )
df_preproc_melt_radio_sep$value <- ifelse(grepl("contrast", df_preproc_melt_radio_sep$value), "contrast enhancement", df_preproc_melt_radio_sep$value)
df_preproc_melt_radio_sep$value <- ifelse(grepl("denoise", df_preproc_melt_radio_sep$value), "denoise", df_preproc_melt_radio_sep$value)
df_preproc_melt_radio_sep$value <- ifelse(grepl("sharpening", df_preproc_melt_radio_sep$value), "sharpening", df_preproc_melt_radio_sep$value)
df_preproc_melt_radio_sep$value <- ifelse(grepl("intensity", df_preproc_melt_radio_sep$value), "intensity enhancement", df_preproc_melt_radio_sep$value)
df_preproc_melt_radio_sep$value <- ifelse(grepl("radiometric", df_preproc_melt_radio_sep$value), "radiometric alignment", df_preproc_melt_radio_sep$value)
df_preproc_melt_radio_sep$value <- ifelse(grepl("no details", df_preproc_melt_radio_sep$value), "no details specified", df_preproc_melt_radio_sep$value)
df_preproc_melt_radio_sep$value <- ifelse(grepl("exposure", df_preproc_melt_radio_sep$value), "exposure enhancement", df_preproc_melt_radio_sep$value)

#radiometric plot

levels(df_preproc_melt_radio_sep$value) <- gsub(" ", "\n", levels(df_preproc_melt_radio_sep$value)) # for line break
preproc_hist_radio <- ggplot(data=subset(df_preproc_melt_radio_sep, !is.na(value)), aes(x=value)) + 
  scale_x_discrete(labels = function(x) str_wrap(x, width = 10)) + 
  geom_bar() + 
  labs( x ="", y="Count") + #title="Accuracy of Ground Control Information",
  theme(plot.title = element_text(color="black", hjust=0.5), text = element_text(size = 14), legend.position="top", 
        legend.text = element_text(size=14), title = element_text(size=14, face = 'bold'))

png(paste(wd_path, "Rplot_preproc_hist_radio.png"), units="in", width=8, height=3, res=300) #print
# insert ggplot code
plot(preproc_hist_radio)
dev.off()



df_preproc_melt_geom <- df_preproc_melt_geom[!(df_preproc_melt_geom$value=="NA"),] # clear NA vals
df_preproc_melt_geom_sep <- separate(data = df_preproc_melt_geom, col = value, into = c("val1", "val2", "val3", "val4", "val5"), sep = ",")
df_preproc_melt_geom_sep <- melt(df_preproc_melt_geom_sep, id = 'key')
df_preproc_melt_geom_sep$variable <- NULL
df_preproc_melt_geom_sep <- df_preproc_melt_geom_sep[!is.na(df_preproc_melt_geom_sep$value),] #delete NA vals
df_preproc_melt_geom_sep$value <- as.character (df_preproc_melt_geom_sep$value )
df_preproc_melt_geom_sep$value <- ifelse(grepl("cropping", df_preproc_melt_geom_sep$value), "cropping", df_preproc_melt_geom_sep$value)
df_preproc_melt_geom_sep$value <- ifelse(grepl("down", df_preproc_melt_geom_sep$value), "downsampling", df_preproc_melt_geom_sep$value)

df_preproc_melt_geom_sep$value <- ifelse(grepl("masking", df_preproc_melt_geom_sep$value), "masking", df_preproc_melt_geom_sep$value)
df_preproc_melt_geom_sep$value <- ifelse(grepl("mosaic", df_preproc_melt_geom_sep$value), "mosaicing", df_preproc_melt_geom_sep$value)

df_preproc_melt_geom_sep$value <- ifelse(grepl("manual IOP", df_preproc_melt_geom_sep$value), "pre-calibration", df_preproc_melt_geom_sep$value)
df_preproc_melt_geom_sep$value <- ifelse(grepl("pp to center", df_preproc_melt_geom_sep$value), "pre-calibration", df_preproc_melt_geom_sep$value)
df_preproc_melt_geom_sep$value <- ifelse(grepl("pre-calib", df_preproc_melt_geom_sep$value), "pre-calibration", df_preproc_melt_geom_sep$value)

df_preproc_melt_geom_sep$value <- ifelse(grepl("affine transformation", df_preproc_melt_geom_sep$value), "image transformation", df_preproc_melt_geom_sep$value)
df_preproc_melt_geom_sep$value <- ifelse(grepl("resamp", df_preproc_melt_geom_sep$value), "image transformation", df_preproc_melt_geom_sep$value)
df_preproc_melt_geom_sep$value <- ifelse(grepl("resize", df_preproc_melt_geom_sep$value), "image transformation", df_preproc_melt_geom_sep$value)
df_preproc_melt_geom_sep$value <- ifelse(grepl("rotat", df_preproc_melt_geom_sep$value), "image transformation", df_preproc_melt_geom_sep$value)
df_preproc_melt_geom_sep$value <- ifelse(grepl("scaling", df_preproc_melt_geom_sep$value), "image transformation", df_preproc_melt_geom_sep$value)
df_preproc_melt_geom_sep$value <- ifelse(grepl("warp", df_preproc_melt_geom_sep$value), "image transformation", df_preproc_melt_geom_sep$value)

df_preproc_melt_geom_sep$value <- ifelse(grepl("undistortion", df_preproc_melt_geom_sep$value), "undistortion", df_preproc_melt_geom_sep$value)

# preprocessing that are related to geometry but not directly applied to the image
df_preproc_melt_geom_sep$value <- ifelse(grepl("detection", df_preproc_melt_geom_sep$value), NA, df_preproc_melt_geom_sep$value)
df_preproc_melt_geom_sep$value <- ifelse(grepl("meta", df_preproc_melt_geom_sep$value), NA, df_preproc_melt_geom_sep$value)

# word fragments to delete
df_preproc_melt_geom_sep$value <- ifelse(grepl("imgs same", df_preproc_melt_geom_sep$value), NA, df_preproc_melt_geom_sep$value)
df_preproc_melt_geom_sep$value <- ifelse(grepl("high dist", df_preproc_melt_geom_sep$value), NA, df_preproc_melt_geom_sep$value)
df_preproc_melt_geom_sep$value <- ifelse(grepl("keep fiducials", df_preproc_melt_geom_sep$value), NA, df_preproc_melt_geom_sep$value)
df_preproc_melt_geom_sep$value <- ifelse(grepl("pseudo", df_preproc_melt_geom_sep$value), NA, df_preproc_melt_geom_sep$value)
df_preproc_melt_geom_sep$value <- ifelse(grepl("sky", df_preproc_melt_geom_sep$value), NA, df_preproc_melt_geom_sep$value)
df_preproc_melt_geom_sep$value <- ifelse(grepl("moving", df_preproc_melt_geom_sep$value), NA, df_preproc_melt_geom_sep$value)
df_preproc_melt_geom_sep$value <- ifelse(grepl("other", df_preproc_melt_geom_sep$value), NA, df_preproc_melt_geom_sep$value)

#geometric plot
levels(df_preproc_melt_geom_sep$value) <- gsub(" ", "\n", levels(df_preproc_melt_geom_sep$value)) # for line break
preproc_hist_geom <- ggplot(data=subset(df_preproc_melt_geom_sep, !is.na(value)), aes(x=value)) + 
  scale_x_discrete(labels = function(x) str_wrap(x, width = 10)) + 
  geom_bar() + 
  labs( x ="", y="Count") + #title="Accuracy of Ground Control Information",
  theme(plot.title = element_text(color="black", hjust=0.5), text = element_text(size = 14), legend.position="top", 
        legend.text = element_text(size=14), title = element_text(size=14, face = 'bold'))

png(paste(wd_path, "Rplot_preproc_hist_geom.png"), units="in", width=8, height=3, res=300) #print
# insert ggplot code
plot(preproc_hist_geom)
dev.off()


