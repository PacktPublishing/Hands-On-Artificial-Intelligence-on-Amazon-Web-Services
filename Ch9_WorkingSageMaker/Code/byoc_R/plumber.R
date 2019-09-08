# What is plumber?
# The plumber R package exposes existing R code as a REST endpoint 
# This is done by decorating existin R code with special comments


#' Ping to show the server is listening
#' @get /ping
function() {
  return('I am alive and listening')
} 

#' Parse input to create user-book matrix and return predictions from model
#' @param req Http request sent
#' @post /invocations
function(req) {
  # Specify location of the trained model on the container
  prefix <- '/opt/ml'
  model_path <- paste(prefix, 'model', sep='/')
    
  # There are a total of 275 users in the dataset; 270 are used for training; specify the user for whom we're going to recommend books
  ind <- 272  
  
  # Load the model
  load(paste(model_path, 'rec_model.RData', sep='/'), verbose = TRUE)

  
  # Read in index of the user for whom we are predicting recommendations
  conn <- textConnection(gsub('\\\\n', '\n', req$postBody))
  data <- read.csv(conn)
  #print("This is data:", data)
  close(conn)
    
  # prepare ratings matrix
  ratings_mat = dcast(data, user_ind~book_ind, value.var = "rating", fun.aggregate=mean)

  # Remove user_ind column
  ratings_mat = as.matrix(ratings_mat[,-1])

  # Reduce the size of the matrix (create a dense matrix)
  ratings_mat = as(ratings_mat, "realRatingMatrix")  
    
  # Get top 5 recommendations for a user or list of users
  pred_bkratings <- predict(rec_model, ratings_mat[ind], n=5)
  
  # Return prediction
  return(as(pred_bkratings, "list"))}