import sublime, sublime_plugin

class GenerateTestSignalsCommand(sublime_plugin.TextCommand):

	def run(self,edit):
		self.generate_test_signals(self.view.file_name())

	def generate_test_signals(self,verilog_file_path) :
		useless_character_list = ['\r','\n','\t']
		verilog_file_name = verilog_file_path.split('/')[-1]
		verilog_file_path_ = ''
		for element in verilog_file_path.split('/')[:-1] : 
			verilog_file_path_ += element + '/'

		generated_file_path = verilog_file_path_ + verilog_file_name[:-2] + '_test.v'

		verilog_file_line_list = []
		with open(verilog_file_path,'r') as verilog_file : 
			for line in verilog_file : 
				verilog_file_line_list.append(line)

		# removing useless characters
		verilog_file_line_list_temp = []
		for line in verilog_file_line_list :
			new_line = ''
			for character in line : 
				if(character not in useless_character_list) :
					new_line += character
			verilog_file_line_list_temp.append(new_line)

		verilog_file_line_list = verilog_file_line_list_temp

		# isolating lines with register or wire declarations
		verilog_file_line_list_temp = []
		for i in range(len(verilog_file_line_list))  :
			line = verilog_file_line_list[i]
			if(line.startswith('reg') or line.startswith('wire')) :
				# append line and line number 
				verilog_file_line_list_temp.append((line[:-1],i+1))

		verilog_file_line_list = verilog_file_line_list_temp
		test_signal_declaration_list_ = []
		test_signal_assignment_list_ = []
		for line in verilog_file_line_list :
			line_string = line[0]
			line_number = line[1]
			[test_signal_declaration_list,test_signal_assignment_list] = self.generate_test_signals_from_line(line_string)

			for element in test_signal_declaration_list :
				test_signal_declaration_list_.append(element)

			test_signal_assignment_list_.append((test_signal_assignment_list,line_number))

		# removing the , after the last test signal declaration
		test_signal_declaration_list_[-1] = test_signal_declaration_list_[-1][:-2]+ '\n'
		generated_file = ''

		# adding test assignment statements
		with open(verilog_file_path) as verilog_file : 
			i = 0
			flag = 0
			multiline_comment_flag = 0
			single_line_comment_flag = 0
			for line in verilog_file : 
				i += 1
				tabs_to_add = ''
				for j in range(self.count_number_of_initial_tabs(line)) :
					tabs_to_add += '\t'

				# multiline comments handling
				if('/*' in line) : 
					multiline_comment_flag = 1
				if('*/' in line and multiline_comment_flag == 1) :
					multiline_comment_flag = 0
				
				# single line comments handling
				if('//' in line) : 
					single_line_comment_flag = 1
				else : 
					single_line_comment_flag = 0

				if(single_line_comment_flag == 0 and multiline_comment_flag == 0) :

					if('module' in line) : 
							flag = 1
					if(');' in line and flag == 1) :
						flag = 0
						generated_file  += tabs_to_add + '// test signals\n'
						for signal_declaration in test_signal_declaration_list_ : 
							generated_file += tabs_to_add + signal_declaration
					
				generated_file += line
				
				if(single_line_comment_flag == 0 and multiline_comment_flag == 0) :
						
					for signal_assignment in test_signal_assignment_list_:
						if(signal_assignment[1] == i) : 
							for element in signal_assignment[0] :
								generated_file += tabs_to_add + element
					

		with open(generated_file_path,'w') as file_ : 
			file_.write(generated_file)

	def generate_test_signals_from_line(self,line) :
		l = line.split(' ')[1:]	#removing reg and wire keywords and
		start_of_line = ''

		if(l[0].startswith('[')) : 	#size declarations given
			start_of_line = l[0]
			l = l[1:]

		# removing spaces
		l_temp = []
		ignore_elements_list = ['',',']
		for element in l :
			if(element in ignore_elements_list) :
				pass
			else :
				new_element = ''
				for character in element : 
					if(character != ' ') :
						new_element += character
				l_temp.append(new_element)

		l = l_temp

		# isolating signals
		l_temp = []
		for element in l : 
			for signal in element.split(',') : 
				if(signal != '') :
					l_temp.append(signal)
		l = l_temp

		test_signal_declaration_list = []
		for signal in l :
			test_signal_declaration_list.append('output wire ' + start_of_line + ' ' + signal + '_test,\n')

		test_signal_assignment_list = []
		for signal in l : 
			test_signal_assignment_list.append('assign ' + signal + '_test = ' + signal + ';\n')

		return [test_signal_declaration_list,test_signal_assignment_list]

	def count_number_of_initial_tabs(self,line) : 
		i = 0
		while(line[i] == '\t') :
			i += 1
		return i
