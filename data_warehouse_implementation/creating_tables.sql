----------------------------------------------------------
--- Creating Index ---

--Complaints--
CREATE INDEX idx_cc_date_received ON complaints ("Date received");
CREATE INDEX idx_cc_product ON complaints ("Product");
CREATE INDEX idx_cc_sub_product ON complaints ("Sub-product");
CREATE INDEX idx_cc_issue ON complaints ("Issue");
CREATE INDEX idx_cc_sub_issue ON complaints ("Sub-issue");
CREATE INDEX idx_cc_company ON complaints ("Company");
CREATE INDEX idx_cc_state ON complaints ("State");
CREATE INDEX idx_cc_date_sent_to_company ON complaints ("Date sent to company");
CREATE INDEX idx_cc_timely_response ON complaints ("Timely response?");
CREATE INDEX idx_cc_consumer_disputed ON complaints ("Consumer disputed?");
CREATE INDEX idx_cc_compalint_id ON complaints ("Complaint ID");

----------------------------------------------------------

----Dimensions----

--1. Location Dimension--
--creating table
create table location_dimension (
	location_id serial primary key,
	state text
);
--creating index
CREATE INDEX idx_state ON location_dimension(state);
--create constraint
ALTER TABLE location_dimension
ADD CONSTRAINT unique_state_constraint UNIQUE (state);

----------------

--2.Date Dimension--
-- Create date_dimension table
CREATE TABLE date_dimension (
    date_id SERIAL PRIMARY KEY,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    day INTEGER NOT NULL
);
--Create indexes for better performance
CREATE INDEX date_dimension_year_index ON date_dimension(year);
CREATE INDEX date_dimension_month_index ON date_dimension(month);
CREATE INDEX date_dimension_day_index ON date_dimension(day);

----------------

--3. Yeaer Dimension --
-- Create year_dimension table
CREATE TABLE year_dimension (
    year_id SERIAL PRIMARY KEY,
    year INTEGER NOT NULL
);
-- Create an index for better performance
CREATE INDEX year_dimension_year_index ON year_dimension(year);

----------------

--4.Company Dimension--
--Creating Table
create table company_dimension (company_id serial primary key, company text);
--Creating Index
CREATE INDEX idx_company ON company_dimension(company);
INSERT INTO company_dimension (Company) VALUES ('');
-- Add a unique constraint to the company column
ALTER TABLE company_dimension
ADD CONSTRAINT unique_company_constraint UNIQUE (company);


--5.Category Dimension--
--Create Table
create table category_dimension (
	category_id serial primary key, product text,
	sub_product text, issue text, sub_issue text);
--Create Index
CREATE INDEX idx_product ON category_dimension(product);
CREATE INDEX idx_sub_product ON category_dimension(sub_product);
CREATE INDEX idx_issue ON category_dimension(issue);
CREATE INDEX idx_sub_issue ON category_dimension(sub_issue);
-- Add a unique constraint to the combination of columns
ALTER TABLE category_dimension
ADD CONSTRAINT unique_category_constraint UNIQUE (product, sub_product, issue, sub_issue);


--A. Population Fact --
-- Create population_fact table
CREATE TABLE population_fact (
    population_id SERIAL PRIMARY KEY,
    year_id INTEGER NOT NULL,
    location_id INTEGER NOT NULL,
    population_over_18 NUMERIC NOT NULL,
    population_over_65 NUMERIC NOT NULL,
    employed_population NUMERIC NOT NULL,
    unemployed_population NUMERIC NOT NULL,
    CONSTRAINT fk_population_fact_year
        FOREIGN KEY (year_id)
        REFERENCES year_dimension (year_id),
    CONSTRAINT fk_population_fact_location
        FOREIGN KEY (location_id)
        REFERENCES location_dimension (location_id)
);
CREATE INDEX population_fact_year_index ON population_fact(year_id);
CREATE INDEX population_fact_location_index ON population_fact(location_id);


----------------


--B. Complaint Fact--
--Create Complaint Fact Table
CREATE TABLE complaint_fact (
    complain_id SERIAL PRIMARY KEY,
    date_id_sent INT,
	date_id_received int, 
    category_id INT,
    company_id INT,
    location_id INT,
	timely_response int,
	consumer_disputed int,
    CONSTRAINT fk_date_sent FOREIGN KEY (date_id_sent) REFERENCES date_dimension(date_id),
    CONSTRAINT fk_date_received FOREIGN KEY (date_id_received) REFERENCES date_dimension(date_id),
    CONSTRAINT fk_category FOREIGN KEY (category_id) REFERENCES category_dimension(category_id),
    CONSTRAINT fk_company FOREIGN KEY (company_id) REFERENCES company_dimension(company_id),
    CONSTRAINT fk_location FOREIGN KEY (location_id) REFERENCES location_dimension(location_id)
);
-- Creating Indexes
CREATE INDEX idx_ct_complain_id ON complaint_fact (complain_id);
CREATE INDEX idx_ct_date_sent ON complaint_fact (date_id_sent);
CREATE INDEX idx_ct_date_received ON complaint_fact (date_id_received);
CREATE INDEX idx_ct_category_id ON complaint_fact (category_id);
CREATE INDEX idx_ct_company_id ON complaint_fact (company_id);
CREATE INDEX idx_ct_location_id ON complaint_fact (location_id);