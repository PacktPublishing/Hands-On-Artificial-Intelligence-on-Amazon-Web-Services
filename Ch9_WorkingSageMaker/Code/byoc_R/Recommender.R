# Load the required libraries
# Bring in the library to create user book matrix
library(reshape2)
# Bring in the library to compute cosine similarity between users
library(recommenderlab)
# Bring in the library to work with datasets (join, filter etc.)
library(dplyr)

library(plumber)
library(jsonlite)

# Define location on the container where training data, model and output will be stored
prefix <- '/opt/ml'
input_path <- paste(prefix, 'input/data', sep='/')
output_path <- paste(prefix, 'output', sep='/')
model_path <- paste(prefix, 'model', sep='/')
param_path <- paste(prefix, 'input/config/hyperparameters.json', sep='/') #similarity method and number of nearest neighbors

# Channel holding training data
channel_name = 'train'
training_path <- paste(input_path, channel_name, sep='/')


# Define training function
train <- function() {
  
  # Read in hyperparameters
  training_params <- read_json(param_path)
  
  # Similarity Method
  if (!is.null(training_params$method)) {
    method <- training_params$method }
  else {
    method <- 'Cosine'}
  
  # Number of nearest neighbors
  if (!is.null(training_params$nn)) {
    nn <- as.numeric(training_params$nn) }
  else {
    nn <- 10 }
  
  # Number of users to train
  if (!is.null(training_params$n_users)) {
    n_users <- as.numeric(training_params$n_users) }
  else {
    n_users <- 190 }
  
  # Read the user book ratings 
  training_files = list.files(path=training_path, full.names=TRUE, pattern='*.csv')
  training_test_data = do.call(rbind, lapply(training_files, read.csv))

  # Create book ratings matrix
  ratings_mat = dcast(training_test_data, user_ind~book_ind, value.var = "rating", fun.aggregate=mean)

  # Remove user_ind column
  ratings_mat = as.matrix(ratings_mat[,-1])

  # Reduce the size of the matrix (create a dense matrix)
  ratings_mat = as(ratings_mat, "realRatingMatrix")  
    
  print(paste("Ratings Matrix size: ", nrow(ratings_mat)))  
  
  # Train the model on book ratings - User Based Collaborative Filtering 
  # For each of the users, identify 10 similar users based on distance between their vectors (defined by book ratings) 
  rec_model = Recommender(ratings_mat[1:n_users], method = "UBCF", param=list(method=method, nn=nn))
  
  # Generate outputs
  #attributes(rec_model)$class <- 'cosinesimilarity'
  save(rec_model, file=paste(model_path, 'rec_model.RData', sep='/'))
  print(summary(rec_model))
  write('success', file=paste(output_path, 'success', sep='/'))}


# Define scoring function
serve <- function() {
  app <- plumb(paste(prefix, 'plumber.R', sep='/'))
  app$run(host='0.0.0.0', port=8080)}

# Parse commandline arguments - depending on whether the command is train or serve, the corresponding functions are executed
args <- commandArgs()
if (any(grepl('train', args))) {
  train()}
if (any(grepl('serve', args))) {
  serve()}