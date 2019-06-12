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
  
  # Load the model
  load(paste(model_path, 'rec_model.RData', sep='/'))
  
  # Read in index of the user for whom we are predicting recommendations
  conn <- textConnection(gsub('\\\\n', '\n', req$postBody))
  data <- read.csv(conn)
  print("This is data:", data)
  close(conn)
  
  # Get top 5 recommendations for a user or list of users
  pred_bkratings <- predict(rec_model, ratings_mat[data], n=5)
  
  # Return prediction
  return(as(pred_bkratings, "list"))}