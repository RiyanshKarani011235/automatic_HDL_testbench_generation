import sublime, sublime_plugin

class GenerateWrapperTestBenchCommand(sublime_plugin.TextCommand) : 
	def run(self,edit) : 	
		self.parse_verilog_module()
		test_bench = self.generate_test_bench()

		test_bench_file_name = ''
		for element in self.view.file_name().split('/')[:-1] : 
			test_bench_file_name += element + '/'
		test_bench_file_name += self.view.file_name().split('/')[-1].split('.')[0] + '_tb.v'

		with open(test_bench_file_name,'w') as test_bench_file : 
			test_bench_file.write(test_bench)

	def parse_verilog_module(self) :
		verilog_file_line_list = []
		with open(self.view.file_name(),'r') as verilog_file : 
			for line in verilog_file : 
				verilog_file_line_list.append(line)

		flag = 0
		parameter_flag = 0
		single_line_comment_flag = 0
		multiline_comment_flag = 0
		signal_declarations_list = []
		module_name = ''
		
		for line in verilog_file_line_list : 

			# multiline comments handling
			if('/*' in line) : 
				multiline_comment_flag = 1
			if('*/' in line and multiline_comment_flag == 1) :
				multiline_comment_flag = 0
			
			# single line comments handling
			if(self.remove_useless_characters(line,['\t']).startswith('//')) : 
				single_line_comment_flag = 1
			else : 
				single_line_comment_flag = 0

			if(multiline_comment_flag == 0) :
				if(single_line_comment_flag == 0) : 
					if 'module' in line and 'endmodule' not in line and flag == 0 : 
						flag = 1
						if '#' in line : 
							parameter_flag = 1
						# getting the module name
						if 'endmodule' not in line :
							line_list = line.split(' ')
							line_list_temp = []
							for element in line_list : 
								if element != '' and '#' not in element:
									line_list_temp.append(element)
							line_list = line_list_temp
							if line_list[-1] == '(' : 
								module_name = line_list[-2]
							elif '(' in line_list [-1] : 
								module_name = line_list[-1].split('(')[0]
								module_name = self.remove_useless_characters(module_name,[' '])
							else :
								module_name = line_list[-1]
					
					elif ')' in line and parameter_flag == 1 : 
						parameter_flag = 0
					elif ');' in line and flag == 1 : 
						flag = 0
					else : 
						if(flag == 1 and parameter_flag == 0) : 
							signal_declarations_list.append(line)
				else : 
					if(flag == 1) : 
						signal_declarations_list.append(line)

		signal_declarations_list_temp = []
		for signal_declaration in signal_declarations_list : 
			signal_declarations_list_temp.append(self.remove_useless_characters(signal_declaration,['\r','\n','\t',',']))
		
		signal_declarations_list = signal_declarations_list_temp
		signal_declarations_list_temp = []

		for signal_declaration in signal_declarations_list : 
			signal_declarations_list_temp.append(signal_declaration.split(' '))

		signal_declarations_list = signal_declarations_list_temp
		signal_declarations_list_temp = []
		
		for signal_declaration in signal_declarations_list : 
			signal_declarations_list_temp.append([])
			for element in signal_declaration : 
				if(element != '') : 
					signal_declarations_list_temp[-1].append(element)

		signal_declarations_list = signal_declarations_list_temp
		signal_declarations_list_temp = []

		for signal_declaration in signal_declarations_list : 
			if signal_declaration != [] : 
				signal_declarations_list_temp.append(signal_declaration)

		signal_declarations_list = signal_declarations_list_temp

		self.module_name = module_name
		self.signal_declarations_list = signal_declarations_list

		for element in self.signal_declarations_list : 
			print(element)

	def generate_test_bench(self) : 
		return_string = ''
		return_string += '`include "' + self.view.file_name().split('/')[-1] + '"\n\n'
		return_string += 'module test_bench();\n'

		for signal_declaration in self.signal_declarations_list : 
			return_string += '\t'
			
			if '//' in signal_declaration[0] : 
				# comment
				for element in signal_declaration : 
					return_string += element + ' '
				return_string += '\n'
			elif signal_declaration[0] == 'input' : 
				# input
				return_string += 'reg ' + signal_declaration[-1] + ';\n'
			elif signal_declaration[0] == 'output' : 
				# output
				return_string += 'wire ' + signal_declaration[-1] + ';\n'
		return_string += '\n'

		return_string += '\t// module instantiation\n'
		return_string += '\t' + self.module_name + ' ' + self.module_name + '_instance1 ' '(\n'
		for signal_declaration in self.signal_declarations_list : 
			return_string += '\t\t'
			if not self.remove_useless_characters(signal_declaration[0],['\t']).startswith('//') : 
				for element in signal_declaration : 
					return_string += element + ' '
				return_string += '\n'
			else :
				return_string += signal_declaration[-1] + '(' + signal_declaration[-1] + '),\n'

		# remove the final ,
		return_string = return_string[:-2] + '\n'
		return_string += '\t);\n\n'

		#add dumpfile and dumpvars compiler directives
		return_string += '\tinitial begin\n\t\t$dumpfile("simulation.vcd");\n\t\t$dumpvars(0,\n'
		for signal_declaration in self.signal_declarations_list : 
			if not self.remove_useless_characters(signal_declaration[0],['\t']).startswith('//') : 
				return_string += '\t\t\t' + signal_declaration[-1] + ',\n'
			else : 
				return_string += '\t\t\t'
				for element in signal_declaration : 
					return_string += element + ' '
				return_string += '\n'
		#remove the final ,
		return_string = return_string[:-2] + '\n\t\t);\n\tend\n\n'

		return_string += '\tinitial begin\n'
		return_string += '\t\t// initializing registers\n'

		for signal_declaration in self.signal_declarations_list : 
			if(signal_declaration[0] == 'input') : 
				return_string += '\t\t' + signal_declaration[-1] + ' = 0;\n'

		return_string += '\n\t\t// add stimulus here\n\n\n\tend\n\nendmodule'
		return return_string

	def remove_useless_characters(self,string,useless_character_list) : 
		return_string = ''
		for character in string : 
			if character not in useless_character_list : 
				return_string += character

		return return_string