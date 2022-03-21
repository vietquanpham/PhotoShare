CREATE DATABASE IF NOT EXISTS photoshare;
USE photoshare;

DROP TABLE IF EXISTS Tagged CASCADE;
DROP TABLE IF EXISTS Likes CASCADE;
DROP TABLE IF EXISTS Friendships CASCADE;
DROP TABLE IF EXISTS Comments CASCADE;
DROP TABLE IF EXISTS Tags CASCADE;
DROP TABLE IF EXISTS Pictures CASCADE;
DROP TABLE IF EXISTS Albums CASCADE;
DROP TABLE IF EXISTS Users CASCADE;

CREATE TABLE Users (
  user_id int4 AUTO_INCREMENT,
  email varchar(255) NOT NULL UNIQUE,
  password varchar(255) NOT NULL,
  first_name varchar(255) NOT NULL,
  last_name varchar(255) NOT NULL,
  dob date NOT NULL,
  gender varchar(255),
  hometown varchar(255),
  CONSTRAINT users_pk PRIMARY KEY (user_id)
);

CREATE TABLE Albums (
  album_id int4 AUTO_INCREMENT,
  name varchar(255) NOT NULL,
  user_id int4 NOT NULL,
  date_created date NOT NULL,
  INDEX uid (user_id),
  CONSTRAINT albums_pk PRIMARY KEY (album_id),
  FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
);

CREATE TABLE Pictures (
  picture_id int4 AUTO_INCREMENT,
  album_id int4 NOT NULL,
  user_id int4 NOT NULL,
  imgdata longblob NOT NULL,
  caption varchar(2000),
  INDEX uid (user_id),
  INDEX aid (album_id),
  CONSTRAINT pictures_pk PRIMARY KEY (picture_id),
  FOREIGN KEY (album_id) REFERENCES Albums(album_id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
);

CREATE TABLE Tags (
  tag_name varchar(30),
  CONSTRAINT tags_pk PRIMARY KEY (tag_name)
);

CREATE TABLE Comments (
  comment_id int4 AUTO_INCREMENT,
  text varchar(2000) NOT NULL,
  user_id int4 NOT NULL,
  picture_id int4 NOT NULL,
  date_created date NOT NULL,
  INDEX uid (user_id),
  INDEX pid (picture_id),
  CONSTRAINT comments_pk PRIMARY KEY (comment_id),
  FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
  FOREIGN KEY (picture_id) REFERENCES Pictures(picture_id) ON DELETE CASCADE
);

CREATE TABLE Friendships (
  user_id int4,
  friend_id int4,
  INDEX fid (friend_id),
  CONSTRAINT friendships_pk PRIMARY KEY (user_id, friend_id),
  FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
  FOREIGN KEY (friend_id) REFERENCES Users(user_id) ON DELETE CASCADE,
  CHECK (user_id <> friend_id)
);

CREATE TABLE Likes (
  user_id int4,
  picture_id int4,
  INDEX uid (user_id),
  INDEX pid (picture_id),
  CONSTRAINT likes_pk PRIMARY KEY (user_id, picture_id),
  FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
  FOREIGN KEY (picture_id) REFERENCES Pictures(picture_id) ON DELETE CASCADE
);

CREATE TABLE Tagged (
  picture_id int4,
  tag_name varchar(30),
  CONSTRAINT tagged_pk PRIMARY KEY (picture_id, tag_name),
  FOREIGN KEY (picture_id) REFERENCES Pictures(picture_id) ON DELETE CASCADE,
  FOREIGN KEY (tag_name) REFERENCES Tags(tag_name) ON DELETE CASCADE
);
