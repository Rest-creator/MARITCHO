import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../cubit/job_execution_cubit.dart';
import '../cubit/job_execution_state.dart';

class JobExecutionPage extends StatefulWidget {
  final String jobId;
  final String workerId;

  const JobExecutionPage({
    super.key,
    required this.jobId,
    required this.workerId,
  });

  @override
  State<JobExecutionPage> createState() => _JobExecutionPageState();
}

class _JobExecutionPageState extends State<JobExecutionPage> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Job Execution')),
      body: BlocConsumer<JobExecutionCubit, JobExecutionState>(
        listener: (context, state) {
          if (!mounted) return; // Engineering Standard: Async Gap Safety
          
          if (state is JobExecutionSuccess) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text(state.message)),
            );
          } else if (state is JobExecutionFailure) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text('Error: \${state.errorMessage}'), backgroundColor: Colors.red),
            );
          }
        },
        builder: (context, state) {
          return Padding(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const Text(
                  'Record your arrival before starting work.',
                  style: TextStyle(fontSize: 16),
                ),
                const SizedBox(height: 24),
                ElevatedButton.icon(
                  onPressed: state is JobExecutionLoading
                      ? null
                      : () => context.read<JobExecutionCubit>().submitCheckIn(
                            jobId: widget.jobId,
                            workerId: widget.workerId,
                            // Dummy GPS coordinates for now
                            latitude: -20.1438,
                            longitude: 28.5828,
                          ),
                  icon: const Icon(Icons.location_on),
                  label: const Text('Check In (Offline Supported)'),
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.all(16.0),
                  ),
                ),
                const SizedBox(height: 24),
                ElevatedButton.icon(
                  onPressed: state is JobExecutionLoading
                      ? null
                      : () => context.read<JobExecutionCubit>().submitPhoto(
                            jobId: widget.jobId,
                            filePath: '/dummy/path/photo.jpg',
                            photoType: 'BEFORE',
                          ),
                  icon: const Icon(Icons.camera_alt),
                  label: const Text('Take Before Photo'),
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.all(16.0),
                  ),
                ),
                if (state is JobExecutionLoading) ...[
                  const SizedBox(height: 24),
                  const Center(child: CircularProgressIndicator()),
                ]
              ],
            ),
          );
        },
      ),
    );
  }
}
