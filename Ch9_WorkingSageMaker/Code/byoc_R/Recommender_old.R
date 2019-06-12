# Recommender system in R (User Based Collaborative Filtering)


################# Data Preparation ##################################

## these should be part of docker file
install.packages("reshape2")
install.packages("recommenderlab")

# Load the cleaned (remove outliers) book ratings created by object2vec_bookratings_reco
bkratings = read.csv("C:/Users/strip009/Desktop/Planning/Personal/Books/Chp9_WorkingWithSageMaker/Data/ClndBookRatings.csv")

sel_bkratings <- bkratings %>% dplyr::select(user_ind, book_ind, BookRating)

# Get users who have rated at least 100 books
grp_usr <- group_by(sel_bkratings, user_ind) %>% summarize(count_ratings=n()) %>% filter(count_ratings >= 100)
# You have ~194 users

fil_bkratings <- sel_bkratings %>% filter(user_ind %in% grp_usr$user_ind)
# we have 38,857 usr book combinations


# Create train and test datasets
# To get repeatable data
set.seed(275) 

train_ratings <- sample_frac(fil_bkratings, 0.8)
train_index <- as.numeric(rownames(train_ratings))
test_ratings <- fil_bkratings[-train_index, ]
write.csv(train_ratings, file = "train_ratings_r.csv", row.names = F)
write.csv(test_ratings, file = "test_ratings_r.csv", row.names = F)

train_test_files = list.files(path='.', full.names = TRUE, pattern='*.csv')
train_test_data = do.call(rbind, lapply(train_test_files, read.csv))


# Create book ratings matrix
ratings_mat = dcast(train_test_data, user_ind~book_ind, value.var = "BookRating", fun.aggregate=mean)

ratings_mat['191', 'user_ind']

bkratings %>% filter(user_ind == 2480) %>% write.csv(file = "2480_ratings.csv", row.names = F)

# Remove user_ind column
ratings_mat = as.matrix(ratings_mat[,-1])

# Reduce the size of the matrix (create a dense matrix)
ratings_mat = as(ratings_mat, "realRatingMatrix")

# Train the model on book ratings - User Based Collaborative Filtering 
# For each of the users, identify 10 similar users based on distance between their vectors (defined by book ratings) 
model = Recommender(ratings_mat[1:190], method = "UBCF", param=list(method='Cosine',nn=10))

# Get top 5 recommendations for first user

#pred_bkratings = predict(model, ratings_mat[191], n=5)
pred_bkratings = predict(model, ratings_mat[192], type='ratingMatrix')

RMSE(as(ratings_mat[192], "matrix"), as(pred_bkratings, "matrix"), na.rm=FALSE)
pred_bklst <- as(pred_bkratings, "list")
df_pred <- data.frame(pred_bklst)
colnames(df_pred) = "book_rating_pred"

df_true <- data.frame(as(ratings_mat[192], "list"))
colnames(df_true) = "book_rating_true"

t4 <- subset(df_pred, row.names(df_pred) %in% row.names(df_true))
#x <- subset(dataset, rownames(dataset) == names)


#df_top5 = data.frame(pred_bklst)
#colnames(df_top5) = "book_ind"

#df_top5$book_ind=as.numeric(levels(df_top5$book_ind))
#book_info=left_join(df_top5, bkratings, by="book_ind")
#distinct(book_info, BookTitle)

# Analysis...#TO DO
hist(getRatings(ratings_mat[191]), breaks='FD')

user_mat = as(ratings_mat[191], "matrix")
df_user_ratings = as(ratings_mat[191], "data.frame")




###############################################################################

# Load the required libraries
# Bring in the library to create user book matrix
library(reshape2)
# Bring in the library to compute cosine similarity between users
library(recommenderlab)
# Bring in the library to work with datasets (join, filter etc.)
library(dplyr)

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
  
  # Bring in data
  training_files = list.files(path=training_path, full.names=TRUE)
  training_data = do.call(rbind, lapply(training_files, read.csv))
  
  # Create book ratings matrix
  ratings_mat = dcast(fil_bkratings, user_ind~book_ind, value.var = "BookRating", fun.aggregate=mean)
  
  # Remove user_ind column
  ratings_mat = as.matrix(ratings_mat[,-1])
  
  # Reduce the size of the matrix (create a dense matrix)
  ratings_mat = as(ratings_mat, "realRatingMatrix")
  
  # Train the model on book ratings - User Based Collaborative Filtering 
  # For each of the users, identify 10 similar users based on distance between their vectors (defined by book ratings) 
  model = Recommender(ratings_mat, method = "UBCF", param=list(method=method,nn=nn))
  
  
  # Generate outputs
  rec_model <- model[!(names(model) %in% c('x', 'residuals', 'fitted.values'))]
  attributes(rec_model)$class <- 'cosinesimilarity'
  save(rec_model, file=paste(model_path, 'rec_model.RData', sep='/'))
  print(summary(rec_model))
  
  # Save fitted values in csv format
  write.csv(model$fitted.values, paste(output_path, 'data/fitted_values.csv', sep='/'), row.names=FALSE)
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



# Get the first 200 users
fil_bkratings <- bkratings %>% filter(user_ind <= 200) %>% dplyr::select(user_ind, book_ind, BookRating)

# there are 18,097 books that are rated by 194 users

# Create book ratings matrix
ratings_mat = dcast(fil_bkratings, user_ind~book_ind, value.var = "BookRating", fun.aggregate=mean)

ncol(ratings_mat)

# Remove user_ind column
ratings_mat = as.matrix(ratings_mat[,-1])

# Reduce the size of the matrix (create a dense matrix)
ratings_mat = as(ratings_mat, "realRatingMatrix")

# Normalize the ratings
#ratings_mat = normalize(ratings_mat)

# Train the model on book ratings - User Based Collaborative Filtering 
# For each of the users, identify 10 similar users based on distance between their vectors (defined by book ratings) 
rec_mod = Recommender(ratings_mat, method = "UBCF", param=list(method="Cosine",nn=10))





# Get top 5 recommendations for first user
pred_bkratings = predict(rec_mod, ratings_mat[2], n=5)
pred_bklst <- as(pred_bkratings, "list")
df_top5 = data.frame(pred_bklst)
colnames(df_top5) = "book_ind"

df_top5$book_ind=as.numeric(levels(df_top5$book_ind))
book_info=left_join(df_top5, bkratings, by="book_ind")
distinct(book_info, BookTitle)


###Evaluate model performance by splitting data into train and test datasets###########

e <- evaluationScheme(ratings_mat, method="split", train=0.9, given=3)
# Fit UBCF on train dataset
recmdr <- Recommender(getData(e, "train"), "UBCF")
# making predictions on the test data set
pred_bkratngs <- predict(recmdr, getData(e, "known"), type="ratings")

# obtaining the error metrics 
error <-calcPredictionAccuracy(pred_bkratngs, getData(e, "unknown"))

error