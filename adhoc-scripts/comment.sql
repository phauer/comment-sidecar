CREATE TABLE comments (
  `id` int(11) NOT NULL PRIMARY KEY AUTO_INCREMENT,
  `author` varchar(30) NOT NULL,
  `email` varchar(30) DEFAULT NULL,
  `content` text NOT NULL,
  `reply_to` int(11) DEFAULT NULL,
  `site` varchar(35) NOT NULL,
  `path` varchar(150) NOT NULL,
  `creation_date` timestamp NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
CREATE INDEX read_index ON comments (`site`, `path`, `creation_date`);

SELECT * from comments order by creation_date desc;

INSERT INTO comments (author, email, content, reply_to, site, path, creation_date)
VALUES ("Till", "bla@bla.de", "Super comment", null, "philipphauer.de", "/post-abc/", "2010-05-20 06:52:22"),
  ("Till", "bla@bla.de", "Super comment", null, "philipphauer.de", "/post-abc/", "2010-06-20 06:52:22"),
  ("Till", "bla@bla.de", "Super comment", 1, "philipphauer.de", "/post-abc/", "2010-07-20 06:52:22");