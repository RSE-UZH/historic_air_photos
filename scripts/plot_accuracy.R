
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
options(digits = 5, scipen = 50)
text_size = 9
line_thickness = 0.25
inch_converting =  2.54





wd_path <- "D:/TUD/ReviewPaper/historic_air_photos/figures/acc/"
reviewSheet <- "D:/TUD/ReviewPaper/historic_air_photos/data/Review_Historic_Air_Photos.csv"

# more colors needed? do this: https://www.datanovia.com/en/blog/easy-way-to-expand-color-palettes-in-r/
# Define the number of colors you want
# nb.cols <- length(unique(comp_data$comp_source))
# mycolors <- colorRampPalette(brewer.pal(8, "Set1"))(nb.cols)
# Create a ggplot with 18 colors 
# Use scale_fill_manual: scale_fill_manual(values = mycolors) 



myData = read.csv(file = reviewSheet, header = TRUE, sep = "," ,na.strings=c("","NA"))
class(myData$DEM.resolution..m.) = "Numeric"
class(myData$Orthophoto.resolution..m.) = "Numeric"
class(myData$Residuals.to.comparison..m..avg) = "Numeric"
class(myData$Residuals.to.CPs..m..avg) = "Numeric"
class(myData$Residuals.to.GCPs..m..avg) = "Numeric"

myData$Fiducial.Marks[is.na(myData$Fiducial.Marks)] <- "not specified"
myData$Fiducial.Marks <- factor(myData$Fiducial.Marks)


# Aerial, Satellite, Mix, Terrestrial
# exlude aerial, mix, terrestrial 
myData_Satellite <-myData[!(myData$Data.Type=="Aerial" | myData$Data.Type=="Terrestrial" | myData$Data.Type=="Mix" ),]
myData_Aerial <-myData[!(myData$Data.Type=="Satellite" | myData$Data.Type=="Terrestrial" | myData$Data.Type=="Mix" ),]






# SATELLITE #
# 1.Residuals to comparison, ordered ascending, colored by use of fiducials 
myData_Satellite <- myData_Satellite[order(myData_Satellite$Residuals.to.comparison..m..avg),] #reorder
plt_sat_fid_resid <- ggplot(myData_Satellite, aes(x=1:nrow(myData_Satellite), y=Residuals.to.comparison..m..avg, colour=Fiducial.Marks, shape=Comparison.source.group), na.rm = TRUE, size=2) +
  geom_point()  +  xlim(0,51) + ylim(-15,30) + 
  geom_errorbar(aes(ymin=Residuals.to.comparison..m..avg - Accurcy.comparison..m..avg, ymax=Residuals.to.comparison..m..avg + Accurcy.comparison..m..avg), width=.2,
                position=position_dodge(.9)) + 
  labs(title="Hist. Satellite Images",x ="ID", y = "Residuals to comparison data [m]", shape = "Comparison Src", colour = "Fiducials?") + 
  theme(plot.title = element_text(color="black", hjust=0.5), text = element_text(size = 20))

png(paste(wd_path, "Rplot_Sat_ResidComp_Fiducials.png"), units="in", width=10, height=5, res=300) #print
plot(plt_sat_fid_resid)
dev.off()

print(paste("Number of Vals used in 'Rplot_Sat_ResidComp_Fiducials.png':" , sum(!is.na(myData_Satellite$Residuals.to.comparison..m..avg))))

# ---------------------------------

# 2. Fiducials usage in percentage
# perc number of Not specitifed / no / yes for satellite imagery
perc_sat_fiduc_no = 100 * sum(myData_Satellite$Fiducial.Marks == "no") / length(myData_Satellite$Fiducial.Marks)
perc_sat_fiduc_yes = 100 * sum(myData_Satellite$Fiducial.Marks == "yes") / length(myData_Satellite$Fiducial.Marks)
perc_sat_fiduc_na = 100 * sum(myData_Satellite$Fiducial.Marks == "not specified") / length(myData_Satellite$Fiducial.Marks)

# create pie chart - Ficducials usage in percentage
# Create Data
perc_fiduc_labels <- c("no", "yes", "not specified")
perc_sat_fiduc_vals <- c(perc_sat_fiduc_no, perc_sat_fiduc_yes, perc_sat_fiduc_na)

# create data frame
perc_fiduc_sat_data <- data.frame(perc_fiduc_labels, perc_sat_fiduc_vals)

# Compute the position of labels
perc_fiduc_sat_data <- perc_fiduc_sat_data %>% 
  arrange(desc(perc_fiduc_labels)) %>%
  mutate(prop = perc_sat_fiduc_vals / sum(perc_fiduc_sat_data$perc_sat_fiduc_vals) *100) %>%
  mutate(ypos = cumsum(prop)- 0.5*prop )

# Basic piechart
plt_sat_fid <- ggplot(perc_fiduc_sat_data, aes(x="", y=prop, fill=perc_fiduc_labels)) +
  geom_bar(stat="identity", width=1, color="white") +
  coord_polar("y", start=0) +
  #theme_void() + 
  theme(legend.position="none", plot.title = element_text(color="black", hjust=0.5), text = element_text(size = 20)) +
  geom_text(aes(y = ypos, label = perc_fiduc_labels), color = "white", size=4) +
  labs(title="Usage of Fiducials (Hist. Satellite Images)", x ="", y="")

png(paste(wd_path, "Rplot_Sat_Usage_Fiducials.png"), units="in", width=10, height=5, res=300) #print
plot(plt_sat_fid)
dev.off()

# ---------------------------------



# 3. DEM Resolution / Orthophoto Resolution, Ordered Ascending
myData_Satellite <- myData_Satellite[order(myData_Satellite$DEM.resolution..m., myData_Satellite$Orthophoto.resolution..m.),] #reorder by DEM and Ortho res

# Scatter plot + Histogram on DEM/Ortho resolution
# create own df for this and melt variables to enable color separation
sat_res_data_DEM <- myData_Satellite$DEM.resolution..m
sat_res_data_Ortho <- myData_Satellite$Orthophoto.resolution..m.
sat_res_data_key <- 1:nrow(myData_Satellite)
sat_res_data <- data.frame('id' = sat_res_data_key, "DEM" = sat_res_data_DEM,  "Orthophoto" = sat_res_data_Ortho)

sat_res_data_mm <- melt(sat_res_data, id = 'id')
sat_res_data_mm$value=as.numeric(sat_res_data_mm$value) #important that col contains unique vals

# Scatter plot
plt_sat_out_res <- ggplot(sat_res_data_mm, aes(x=id) , na.rm = TRUE) + 
  geom_point(aes(y=value, color=variable), na.rm = TRUE) + xlim(0,80) + ylim(0,60) + 
  labs(title="Hist. Satellite images: Output resolution [m]",x ="ID", y = "Output resolution [m]", color = "Output")  + 
  theme(plot.title = element_text(color="black", hjust=0.5), text = element_text(size = 20))

png(paste(wd_path, "Rplot_Sat_Output_Resolution.png"), units="in", width=10, height=5, res=300) #print
plot(plt_sat_out_res)
dev.off()

# Histogram
plt_sat_out_res_hist <- ggplot(sat_res_data_mm, aes(x=value, fill=variable)) + 
  geom_histogram(position="identity", bins=20, na.rm = TRUE, alpha = 0.75) + 
  xlim(0,80) + ylim(0,110) +
  labs(title = "Histogram: Hist. Satellite Images: Output resolution [m]", x ="Resolution [m]", y="Count", fill = "Output") + 
  theme(plot.title = element_text(color="black", hjust=0.5), text = element_text(size = 20))

png(paste(wd_path, "Rplot_Sat_Output_Resolution_Histo.png"), units="in", width=10, height=5, res=300) #print
plot(plt_sat_out_res_hist)
dev.off()










# AERIAL # 
# 1. Residuals to comparision, ordered ascending, colored by use of fiducials 
myData_Aerial <- myData_Aerial[order(myData_Aerial$Residuals.to.comparison..m..avg),] #reorder
plt_aerial_fid_resid <- ggplot(myData_Aerial, aes(x=1:nrow(myData_Aerial), y=Residuals.to.comparison..m..avg, shape=Comparison.source.group, colour=Fiducial.Marks ) , na.rm = TRUE) +
  geom_point()  +  xlim(0,125) + ylim(-15,30) +
  geom_errorbar(aes(ymin=Residuals.to.comparison..m..avg - Accurcy.comparison..m..avg, ymax=Residuals.to.comparison..m..avg + Accurcy.comparison..m..avg), width=.2,
                position=position_dodge(.9)) +
  labs(title="Hist. Aerial Images",x ="ID", y = "Residuals to comparison data [m]", shape = "Comparison Src", colour = "Fiducials?") +
  theme(plot.title = element_text(color="black", hjust=0.5), text = element_text(size = 20))

png(paste(wd_path, "Rplot_Aerial_ResidComp_Fiducials.png"), units="in", width=10, height=5, res=300) #print
plot(plt_aerial_fid_resid)
dev.off()

print(paste("Number of Vals used in 'Rplot_Aerial_ResidComp_Fiducials.png':" , sum(!is.na(myData_Aerial$Residuals.to.comparison..m..avg))))



# ---------------------------------

# 2. Fiducials usage in percentage
# perc number of Not specitifed / no / yes for satellite imagery
perc_aerial_fiduc_no = 100 * sum(myData_Aerial$Fiducial.Marks == "no") / length(myData_Aerial$Fiducial.Marks)
perc_aerial_fiduc_yes = 100 * sum(myData_Aerial$Fiducial.Marks == "yes") / length(myData_Aerial$Fiducial.Marks)
perc_aerial_fiduc_na = 100 * sum(myData_Aerial$Fiducial.Marks == "not specified") / length(myData_Aerial$Fiducial.Marks)
 
# create pie chart - Ficducials usage in percentage
# Create Data
perc_fiduc_labels <- c("no", "yes", "not specified")
perc_aerial_fiduc_vals <- c(perc_aerial_fiduc_no, perc_aerial_fiduc_yes, perc_aerial_fiduc_na)

# create data frame
perc_fiduc_aerial_data <- data.frame(perc_fiduc_labels, perc_aerial_fiduc_vals)

# Compute the position of labels
perc_fiduc_aerial_data <- perc_fiduc_aerial_data %>% 
  arrange(desc(perc_fiduc_labels)) %>%
  mutate(prop = perc_aerial_fiduc_vals / sum(perc_fiduc_aerial_data$perc_aerial_fiduc_vals) *100) %>%
  mutate(ypos = cumsum(prop)- 0.5*prop )

# Basic piechart
plt_aerial_fid <- ggplot(perc_fiduc_aerial_data, aes(x="", y=prop, fill=perc_fiduc_labels)) +
  geom_bar(stat="identity", width=1, color="white") +
  coord_polar("y", start=0) +
  #theme_void() + 
  theme(legend.position="none", plot.title = element_text(color="black", hjust=0.5), text = element_text(size = 20)) +
  geom_text(aes(y = ypos, label = perc_fiduc_labels), color = "white", size=4) +
  labs(title="Usage of Fiducials (Hist. Aerial images)", x ="", y="")

png(paste(wd_path, "Rplot_Aerial_Usage_Fiducials.png"), units="in", width=10, height=5, res=300) #print
plot(plt_aerial_fid)
dev.off()

# ---------------------------------



# 3. DEM Resolution / Orthophoto Resolution, Ordered Ascending
myData_Aerial <- myData_Aerial[order(myData_Aerial$DEM.resolution..m., myData_Aerial$Orthophoto.resolution..m.),] #reorder by DEM and Ortho res

# Scatterplot + Histogram on DEM/Ortho resolution
# create own df for this and melt variables to enable color seperation
aerial_res_data_DEM <- myData_Aerial$DEM.resolution..m
aerial_res_data_Ortho <- myData_Aerial$Orthophoto.resolution..m.
aerial_res_data_key <- 1:nrow(myData_Aerial)
aerial_res_data <- data.frame('id' = aerial_res_data_key, 'DEM' = aerial_res_data_DEM, 'Orthophoto' = aerial_res_data_Ortho)
aerial_res_data_mm <- melt(aerial_res_data, id = 'id')

aerial_res_data_mm$value=as.numeric(aerial_res_data_mm$value) #important that col contains unique vals


# Scatter plot
plt_aerial_out_res <- ggplot(aerial_res_data_mm, aes(x=id)) + 
  geom_point(aes(y=value, color=variable), na.rm = TRUE)+ xlim(0,250) + ylim(0,60) + 
  labs(title="Hist. Aerial images: Output resolution [m]",x ="ID", y = "Output resolution [m]", color = "Output")  + 
  theme(plot.title = element_text(color="black", hjust=0.5), text = element_text(size = 20))

png(paste(wd_path, "Rplot_Aerial_Output_Resolution.png"), units="in", width=10, height=5, res=300) #print
plot(plt_aerial_out_res)
dev.off()

# Histogram
plt_aerial_out_res_hist <- ggplot(aerial_res_data_mm, aes(x=value, fill=variable)) + geom_histogram(position="identity", bins=20, na.rm = TRUE, alpha = 0.75) +
  labs(title = "Histogram: Hist. Aerial Images: Output resolution [m]", x ="Resolution [m]", y="Count", fill = "Output") + ylim(0,110) +
  theme(plot.title = element_text(color="black", hjust=0.5), text = element_text(size = 20))

png(paste(wd_path, "Rplot_Aerial_Output_Resolution_Histo.png"), units="in", width=10, height=5, res=300) #print
plot(plt_aerial_out_res_hist)
dev.off()

# 4. Groundcontrol data: type and when used? aerial / satellite
# prep data
gcp_source <- myData$Ground.control.source.group
gcp_source <- as.character(gcp_source)
gcp_source[gcp_source == "?"] <- NA # remove some creepy stuff like "?" -> to NA
gcp_source <- factor(gcp_source)

gcp_accuracy_avg <- myData$Ground.control.accuraxy..m..avg
data_type <- myData$Data.Type
gcp_data <- data.frame("GCP source" = gcp_source, "GCP accuracy (avg) [m]" = gcp_accuracy_avg, "Data Type" = data_type)
gcp_data<-subset(gcp_data, data_type!="Terrestrial" & data_type!="Mix") #drop Terrestrial & Mix
gcp_data<-subset(gcp_data, !is.na(gcp_data$GCP.accuracy..avg...m.) & !is.na(gcp_data$GCP.source)) # drop NA, makes no sense to print this information


gcp_data <- gcp_data[order(gcp_data$GCP.source),] # sort dataset by accuracy



print(paste("Number of area-based GCP sources in 'aerial':" , length(which(gcp_data$GCP.source=='area-based' & gcp_data$Data.Type=='Aerial'))))
print(paste("Number of point-based GCP sources in 'aerial':" , length(which(gcp_data$GCP.source=='point-based' & gcp_data$Data.Type=='Aerial'))))
print(paste("Number of area-based GCP sources in 'satellite':" , length(which(gcp_data$GCP.source=='area-based' & gcp_data$Data.Type=='Satellite'))))
print(paste("Number of point-based GCP sources in 'satellite':" , length(which(gcp_data$GCP.source=='point-based' & gcp_data$Data.Type=='Satellite'))))



# Histogram: Source Ground Control Information
plt_gcp_bar_src_dt <- ggplot(gcp_data, aes(x=GCP.source, fill=Data.Type), na.rm = TRUE) + 
  geom_bar (position="identity", alpha = 0.75) +
  labs(x ="GCP source", y="Count", fill = "Data Type:") + #title = "Source of Ground Control Information"
  theme(plot.title = element_text(color="black", hjust=0.5), text = element_text(size = 20), legend.position="top", 
        legend.text = element_text(size=14), title = element_text(size=14, face = 'bold'))
print(paste("Number of Datasets used in 'Rplot_source_groundcontrol.png':" , nrow(gcp_data)))

plt_gcp_hist_acc_src <- ggplot(gcp_data, aes(x=GCP.accuracy..avg...m., fill = GCP.source), na.rm = TRUE) + 
  geom_histogram(position="identity", bins = 20, alpha = 0.75) +
  #xlim(0,100) + ylim(0,20) +
  labs( x ="Accuracy [m]", y="Count", fill = "GCP Source:") + #title="Accuracy of Ground Control Information",
  theme(plot.title = element_text(color="black", hjust=0.5), text = element_text(size = 20), legend.position="top", 
        legend.text = element_text(size=14), title = element_text(size=14, face = 'bold'))

# fuse both graphics
#https://rdrr.io/cran/ggpubr/man/rremove.html
plt_gcp_bar_hist_src_acc <- ggarrange(plt_gcp_bar_src_dt, plt_gcp_hist_acc_src + rremove("y.title"), labels = c("A", "B"), ncol = 2, nrow = 1)
plt_gcp_bar_hist_src_acc <- annotate_figure(plt_gcp_bar_hist_src_acc, top = text_grob("Source / Accuracy of Ground Control Data", color = "black", size = 20)) #face = "bold", 
plt_gcp_bar_hist_src_acc <- annotate_figure(plt_gcp_bar_hist_src_acc, bottom = text_grob(paste("Considered datasets:", nrow(gcp_data), "(no NA)" ), color = "black", size = 14))
plt_gcp_bar_hist_src_acc

png(paste(wd_path, "Rplot_src_acc_gc.png"), units="in", width=10, height=5, res=300) #print
plot(plt_gcp_bar_hist_src_acc)
dev.off()





# 5. Comparison data: source (simplified) and when used? aerial / satellite
# prep data 
comp_source <- myData$Comparison.data.simplified
comp_source <- as.character(comp_source)
comp_source[comp_source == "?"] <- NA # remove some creepy stuff like "?" -> to NA
# make things a bit easier and simplify the tags a bit more #20.5.22
comp_source[comp_source == "GCP"] <- "GCPs" # remove some creepy stuff like "?" -> to NA
comp_source[comp_source == "GCPs"] <- "GCPs" # remove some creepy stuff like "?" -> to NA
comp_source[comp_source == "CPs"] <- "CPs" # remove some creepy stuff like "?" -> to NA

# more unique
comp_source[comp_source == "ALS-DEM, TLS"] <- "DEM"
comp_source[comp_source == "ALS-DEM"] <- "DEM"
comp_source[comp_source == "ICESat"] <- "Altimetry"
comp_source[comp_source == "ICESat, ALS-DEM"] <- "diverse"
comp_source[comp_source == "Imgs, ALS-DEM"] <- "DEM"
comp_source[comp_source == "Imgs, SRTM, ICESat"] <- "diverse"
comp_source[comp_source == "StereoDEM"] <- "DEM"
comp_source[comp_source == "TLS"] <- "DEM"

comp_source <- factor(comp_source)
comp_accuracy_avg <- myData$Accurcy.comparison..m..avg
data_type <- myData$Data.Type
comp_source_group <- myData$Comparison.source.group

comp_data <- data.frame(comp_source, comp_accuracy_avg, data_type, comp_source_group)
comp_data <- comp_data[order(comp_data$comp_accuracy_avg),] #reorder by acc
comp_data_noNA <- subset(comp_data,!is.na(comp_accuracy_avg)) # drop all rows that contain no accuracy information!
comp_data_noNA <- subset(comp_data_noNA, (comp_source_group == 'area-based' | comp_source_group == 'point-based' )) # drop all rows that contain no accuracy information!

plt_compData_src_acc <- ggplot(comp_data_noNA, aes(x = comp_accuracy_avg, y=reorder(comp_source_group,comp_accuracy_avg)), na.rm = TRUE) + 
  #geom_line(aes(colour = comp_source), na.rm = TRUE) + 
  #geom_point(size=2, aes(colour=comp_source), na.rm = TRUE) +
  geom_line(na.rm = TRUE) + #no color
  geom_point(size=2, na.rm = TRUE, aes(colour = comp_source)) + #no color
  scale_x_continuous(trans="log10",breaks = c(0, 0.25, 0.5,1,2,4,6,8,10,25), labels = c(0, "<0.25", 0.5, 1,2,4,6,8,10,25)) +
  labs(title="Accuracy/Source of Comparison Information", x ="Accuracy [m]", y="Source", colour = "Source") +
  theme(plot.title = element_text(color="black", hjust=0.5), text = element_text(size = 15))

png(paste(wd_path, "Rplot_acc_src_comp_A.png"), units="in", width=10, height=3, res=300) #print
# insert ggplot code
plot(plt_compData_src_acc)
dev.off()


plt_compData_src_acc <- ggplot(comp_data_noNA, aes(x = comp_accuracy_avg, y=reorder(comp_source,comp_accuracy_avg)), na.rm = TRUE) + 
  #geom_line(aes(colour = comp_source), na.rm = TRUE) + 
  #geom_point(size=2, aes(colour=comp_source), na.rm = TRUE) +
  geom_line(na.rm = TRUE) + #no color
  geom_point(size=2, na.rm = TRUE) + #no color
  scale_x_continuous(trans="log10",breaks = c(0, 0.25, 0.5,1,2,4,6,8,10,25), labels = c(0, "<0.25", 0.5, 1,2,4,6,8,10,25)) +
  labs(title="Accuracy/Source of Comparison Information", x ="Accuracy [m]", y="Source", colour = "Source") +
  theme(plot.title = element_text(color="black", hjust=0.5), text = element_text(size = 15))

png(paste(wd_path, "Rplot_acc_src_comp_B.png"), units="in", width=10, height=3, res=300) #print
# insert ggplot code
plot(plt_compData_src_acc)
dev.off()



#6. GSD Input / Output
myData_dropped_DT <- subset(myData, Data.Type!="Terrestrial" & Data.Type!="Mix") # drop terrestrial and mixed
myData_dropped_DT <- subset(myData_dropped_DT,!is.na(GSD..m.)) # drop all rows that contain no accuracy information!
myData_dropped_DT <- subset(myData_dropped_DT,!is.na(Residuals.to.comparison..m..avg)) # drop all rows that contain no accuracy information!
myData_dropped_DT <- subset(myData_dropped_DT,(GSD..m. <= 10)) # drop all rows that contain no accuracy information!
myData_dropped_DT <- myData_dropped_DT[order(myData_dropped_DT$Residuals.to.comparison..m..avg, myData_dropped_DT$GSD..m.),] #reorder by DEM and Ortho res

iso_0.5 <- data.frame("x" = seq(0, 10, by = 0.1), "y" = seq(0, 50, by = 0.5))
iso_0.25 <- data.frame("x" = seq(0, 10, by = 0.1), "y" = seq(0, 25, by = 0.25))
iso_0.1 <- data.frame("x" = seq(0, 10, by = 0.1), "y" = seq(0, 10, by = 0.1))


plt_residuals_gsd <- ggplot() +
  geom_point(aes(x = myData_dropped_DT$GSD..m., y=myData_dropped_DT$Residuals.to.comparison..m..avg, colour=myData_dropped_DT$Data.Type)) + 
  geom_line(aes(x=iso_0.5$x, y=iso_0.5$y)) +
  geom_line(aes(x=iso_0.25$x, y=iso_0.25$y)) +
  geom_line(aes(x=iso_0.1$x, y=iso_0.1$y)) +
  ylim(0,20) +
  #scale_x_continuous(trans='log', limits = c(0, 10)) +
  scale_x_continuous(trans="log", breaks = c(0, 0.10, 0.25, 0.5,1,2,4,6,8,10), labels = c(0, 0.10, 0.25, 0.5, 1,2,4,6,8,10)) +
  #labs(title="Residuals to GSD", x ="GSD [m]", y="Residuals [m]", fill = "Data Type") +
  labs(x ="GSD [m]", y="Residuals [m]", colour = "Data Type") + #no title
  theme(plot.title = element_text(color="black", hjust=0.5), text = element_text(size = 15))

png(paste(wd_path, "Rplot_gsd_residuals_without_tl.png"), units="in", width=8, height=3, res=300) #print
# insert ggplot code
plot(plt_residuals_gsd)
dev.off()

#cor.test(myData$GSD..m., myData$Residuals.to.comparison..m..avg, method = c("kendall"))

